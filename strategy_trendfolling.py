import time
from datetime import datetime

from tinkoff.invest import Client, CandleInterval, HistoricCandle, OrderType, OrderDirection
from tinkoff.invest.services import Services
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal, money_to_decimal

from info_requester import InfoRequester
import pandas as pd
from logger import Logger
from asset import Asset
import os
from csv_saver import CSV_Saver



class TrendFolling:
    """ Класс следования стратегии трендфоллинга """

    def __init__(
            self,
            days_back: int,
            timeframe: CandleInterval,
            check_interval: int,
            client: Services,
            assets: list[Asset] = None,
    ):
        """
        :param days_back: с какого дня назад считать
        :param timeframe: временной интервал свеч
        :param check_interval: интервал для проверки свеч (в секундах)
        :param client: клиент
        """

        self.client: Services = client
        self.assets = assets or []
        self.days_back: int = days_back  # 30
        self.timeframe: CandleInterval = timeframe
        self.check_interval: int = check_interval
        self.account_id: int | None = None
        self.info_requester = InfoRequester(self.client)  # ПЕСОЧНИЦА TRUE
        self.is_waiting = False
        self.logger = Logger()
        self.saver = CSV_Saver()

        self.MA_small = 9  # 50
        self.MA_long = 15  # 200


    def start(self):
        """ Подготовка данных к основному циклу """
        if self.account_id is None:
            self.account_id = self.client.users.get_accounts().accounts[0].id
        self.main_loop()

    def add_asset(self, new_asset: Asset):
        """ Добавление нового актива в список отслеживаемых """
        self.assets.append(new_asset)

    def main_loop(self):
        """ Основной цикл стратегии """
        while True:
            os.system('cls')

            for asset in self.assets:
                is_avalible = self.wait_for_open_market(asset=asset)
                if not is_avalible:
                    continue

                data = self.info_requester.get_candles(
                    asset.figi,
                    self.days_back,
                    self.timeframe
                )
                for candle in data:
                    if candle not in asset.candles:
                        asset.candles.append(candle)

                df = self.processed_candles(asset=asset)
                last_signals = df[-1:]

                print()
                print(f"{asset.name} [{asset.figi}] >> CLOSE:{last_signals["close"].values}, "
                      f"MA_{self.MA_small}:{last_signals["MA_small"].values}, "
                      f"MA_{self.MA_long}:{last_signals["MA_long"].values}, "
                      f"RSI:{last_signals["RSI"].values}")

                signal = 0
                if ((last_signals["close"].values[0] > last_signals["MA_small"].values[0])
                        and (last_signals["MA_small"].values[0] > last_signals["MA_long"].values[0])
                        and last_signals["RSI"].values[0] > 50):
                    signal = 1
                if ((last_signals["close"].values[0] < last_signals["MA_small"].values[0])
                        # or (last_signals["MA_small"] > last_signals["MA_long"])
                        or last_signals["RSI"].values[0] < 50):
                    signal = -1

                print(f"\t### SIGNAL: [{signal}]")
                self.saver.write_operation_data(
                    asset.name,
                    asset.figi,
                    self.MA_small,
                    self.MA_long,
                    last_signals["MA_small"].values[0],
                    last_signals["MA_long"].values[0],
                    last_signals["RSI"].values[0],
                    signal
                )

                if signal == 1 and not asset.is_bought:
                    post_order_response = self.client.orders.post_order(
                        figi=asset.figi,
                        quantity=asset.amount,
                        account_id=self.account_id,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        direction=OrderDirection.ORDER_DIRECTION_BUY
                    )
                    asset.is_bought = True
                    print(f"\tПОКУПКА :: [{post_order_response.figi}] {post_order_response.initial_order_price}")
                    # print(post_order_response)

                elif signal == -1 and asset.is_bought:
                    post_order_response = self.client.orders.post_order(
                        figi=asset.figi,
                        quantity=asset.amount,
                        account_id=self.account_id,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        direction=OrderDirection.ORDER_DIRECTION_SELL
                    )
                    asset.is_bought = False
                    print(f"\tПРОДАЖА :: [{post_order_response.figi}] {post_order_response.initial_order_price}")
                    # print(post_order_response)

            # print(f"\n### БАЛАНС: [{float(quotation_to_decimal(self.client.operations.get_positions(account_id=self.account_id).money[0]))}]")
            print()
            self.info_requester.get_money_amount_data(print_=True)
            print(f"\n==========================================")
            time.sleep(self.check_interval)

    def calculate_RSI(self, df: pd.DataFrame):
        """ Функция расчета значения RSI для ряда свеч """
        window = 14  # для ETF
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def wait_for_open_market(self, asset: Asset):
        """ Функция проверки актива на возможность торговли """

        # Переделать. Необходимо, что бы для каждого актива
        # был свой счетчик ожидания, иначе они все будут по часу
        # ждать, надо по 10 мин хотя бы

        while True:
            data = self.client.market_data.get_trading_status(figi=asset.figi)
            if (not data.api_trade_available_flag) or (not data.market_order_available_flag):
                if not asset.is_waiting:
                    asset.is_waiting = True
                    print(f"###  {datetime.now()} :: {asset.name} [{asset.figi}] >> ожидание открытия торговли")
                    self.logger.info(message=f"{asset.name} [{asset.figi}] >> ожидание открытия торговли", module=__name__)
                # time.sleep(60 * 10)
                return False
            else:
                if asset.is_waiting:
                    asset.is_waiting = False
                    print(f"###  {datetime.now()} :: {asset.name} [{asset.figi}] >> зафиксировано открытие торговли")
                    self.logger.info(message=f"{asset.name} [{asset.figi}] >> зафиксировано открытие торговли", module=__name__)
                return True

    def processed_candles(self, asset: Asset):
        """ Создание таблицы с индикаторами MA и RSI, для определения сигнала """
        all_data = {
            "close": []
        }
        for candle in asset.candles:
            all_data["close"].append(quotation_to_decimal(candle.close))

        res = pd.DataFrame(data=all_data)
        res["MA_small"] = res["close"].rolling(self.MA_small).mean()  # 50
        res["MA_long"] = res["close"].rolling(self.MA_long).mean()  # 200
        res["RSI"] = self.calculate_RSI(res)
        return res
