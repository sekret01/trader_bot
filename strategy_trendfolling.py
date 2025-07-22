import time
from datetime import datetime

from tinkoff.invest import Client, CandleInterval, HistoricCandle, OrderType, OrderDirection
from tinkoff.invest.services import Services
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal

from info_requester import InfoRequester
import pandas as pd
from logger import Logger



class TrendFolling:
    """ Класс следования стратегии трендфоллинга """

    def __init__(
            self,
            figi: str,
            days_back: int,
            timeframe: CandleInterval,
            check_interval: int,
            client: Services,
            amount: int
    ):
        """
        :param figi: figi актива
        :param days_back: с какого дня назад считать
        :param timeframe: временной интервал свеч
        :param check_interval: интервал для проверки свеч (в секундах)
        :param client: клиент
        """

        self.client: Services = client
        self.figi: str = figi
        self.days_back: int = days_back  # 30
        self.timeframe: CandleInterval = timeframe
        self.check_interval: int = check_interval
        self.amount = amount
        self.account_id: int | None = None
        self.candles: list[HistoricCandle] = []
        self.info_requester = InfoRequester(self.client)  # ПЕСОЧНИЦА TRUE
        self.bought: bool = False
        self.is_waiting = False
        self.logger = Logger()

        self.MA_small = 9  # 50
        self.MA_long = 15  # 200


    def start(self):
        """ Подготовка данных к циклу """
        if self.account_id is None:
            self.account_id = self.client.users.get_accounts().accounts[0].id

        self.main_loop()

    def main_loop(self):
        """ Основной цикл стратегии """
        while True:

            self.wait_for_open_market()

            data = self.info_requester.get_candles(
                self.figi,
                self.days_back,
                self.timeframe
            )
            for candle in data:
                if candle not in self.candles:
                    self.candles.append(candle)

            df = self.processed_candles()
            last_signals = df[-1:]
            print(last_signals)
            signal = 0
            if ((last_signals["close"].values[0] > last_signals["MA_small"].values[0])
                    and (last_signals["MA_small"].values[0] > last_signals["MA_long"].values[0])
                    and last_signals["RSI"].values[0] > 50):
                signal = 1
            if ((last_signals["close"].values[0] < last_signals["MA_small"].values[0])
                    # or (last_signals["MA_small"] > last_signals["MA_long"])
                    or last_signals["RSI"].values[0] < 50):
                signal = -1

            print(f"### SIGNAL: [{signal}]")

            if signal == 1 and not self.bought:
                post_order_response = self.client.orders.post_order(
                    figi=self.figi,
                    quantity=1,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    direction=OrderDirection.ORDER_DIRECTION_BUY
                )
                self.bought = True
                print("ПОКУПКА")
                print(post_order_response)

            elif signal == -1 and self.bought:
                post_order_response = self.client.orders.post_order(
                    figi=self.figi,
                    quantity=self.amount,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    direction=OrderDirection.ORDER_DIRECTION_SELL
                )
                self.bought = False
                print("ПРОДАЖА")
                print(post_order_response)

            print(f"### БАЛАНС: [{float(quotation_to_decimal(self.client.operations.get_positions(account_id=self.account_id).money[0]))}]")
            time.sleep(self.check_interval)

    def calculate_RSI(self, df):
        window = 14  # для ETF
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def wait_for_open_market(self):
        while True:
            data = self.client.market_data.get_trading_status(figi=self.figi)
            if (not data.api_trade_available_flag) or (not data.market_order_available_flag):
                if not self.is_waiting:
                    self.is_waiting = True
                    print(f"###  {datetime.now()} :: [{self.figi}] >> ожидание открытия торговли")
                    self.logger.info(message=f"[{self.figi}] >> ожидание открытия торговли", module=__name__)
                time.sleep(60 * 10)
            else:
                if self.is_waiting:
                    self.is_waiting = False
                    print(f"###  {datetime.now()} :: [{self.figi}] >> зафиксировано открытие торговли")
                    self.logger.info(message=f"[{self.figi}] >> зафиксировано открытие торговли", module=__name__)
                return

    def processed_candles(self):
        all_data = {
            "close": []
        }
        for candle in self.candles:
            all_data["close"].append(quotation_to_decimal(candle.close))

        res = pd.DataFrame(data=all_data)
        res["MA_small"] = res["close"].rolling(self.MA_small).mean()  # 50
        res["MA_long"] = res["close"].rolling(self.MA_long).mean()  # 200
        res["RSI"] = self.calculate_RSI(res)
        return res
