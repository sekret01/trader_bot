from datetime import timedelta

from tinkoff.invest import CandleInterval, InstrumentType, HistoricCandle, AioRequestError, OrderType, OrderDirection
from tinkoff.invest.services import Services
from tinkoff.invest.utils import now

from typing import Optional
import time
import datetime
import strategies


class CandleTemplate:
    """ Шаблон объекта актива, стратегия которого основана на получении данных свечей """

    def __init__(
            self,
            client: Services,
            figi: str,
            name: str,
            amount: int,
            days_back: int,
            timeframe: CandleInterval,
            check_interval: int,
            type_: InstrumentType,
            strategy: strategies.Strategy
    ) -> None:
        """
        :param client: клиент для отправления запросов API
        :param figi: figi актива
        :param name: название актива
        :param amount: количество, которое необходимо купить или продать
        :param days_back: количество дней для получения исторических свеч
        :param timeframe: промежуток строения свеч
        :param check_interval: временной интервал проверки свеч
        :param type_: тип актива (фонд, акция и тд)
        """

        self.client: Services = client
        self.account_id: int | None = None
        self.figi: str = figi
        self.name: str = name
        self.amount: int = amount
        self.days_back: int = days_back
        self.timeframe: CandleInterval = timeframe
        self.check_interval: int = check_interval
        self.type_: InstrumentType = type_
        self.strategy: strategies.Strategy = strategy
        # self.logger = ...

        self.candles: list[HistoricCandle] = []
        self.is_bought: bool = False
        self.is_waiting_open: bool = False
        self.wait_time: int = 60 * 10

    def start(self) -> None:
        """ Подготовка данных и запуск главного цикла """
        if self.account_id is None:
            self.account_id = self.client.users.get_accounts().accounts[0].id
        self.main_loop()

    def main_loop(self) -> None:
        """ Главный цикл мониторинга актива """
        while True:
            try:
                self.wait_for_open_market()
                self.get_historic_candles()

                self.strategy.prepare_data(candles=self.candles)
                signal = self.strategy.get_signal()
                # logger
                self.action(signal)

            except AioRequestError as ex:
                # logger
                ...

    def action(self, signal: int) -> None:
        """ Принятие решение на основе сигнала """
        # вынести функции в отдельный класс

        if signal == 1 and not self.is_bought:
            post_order_response = self.client.orders.post_order(
                figi=self.figi,
                quantity=self.amount,
                account_id=self.account_id,
                order_type=OrderType.ORDER_TYPE_MARKET,
                direction=OrderDirection.ORDER_DIRECTION_BUY
            )
            self.is_bought = True
            # print(f"\tПОКУПКА :: [{post_order_response.figi}] {post_order_response.initial_order_price}")
            # logger

        elif signal == -1 and self.is_bought:
            post_order_response = self.client.orders.post_order(
                figi=self.figi,
                quantity=self.amount,
                account_id=self.account_id,
                order_type=OrderType.ORDER_TYPE_MARKET,
                direction=OrderDirection.ORDER_DIRECTION_SELL
            )
            self.is_bought = False
            # print(f"\tПРОДАЖА :: [{post_order_response.figi}] {post_order_response.initial_order_price}")
            # logger

        else:
            # logger
            ...

        time.sleep(self.check_interval)

    def get_historic_candles(self) -> None:
        """ Получение свечей по заданным параметрам """
        # logger
        for candle in self.client.get_all_candles(
            from_=now() - timedelta(days=self.days_back),
            to=now(),
            figi=self.figi,
            interval=self.timeframe
        ):
            if not candle in self.candles:
                # if candle.is_complete:
                self.candles.append(candle)
        # logger

    def wait_for_open_market(self):
        """ Ожидание открытия торгов, если они недоступны """
        while True:
            trading_data = self.client.market_data.get_trading_status(figi=self.figi)

            if not (
                trading_data.api_trade_available_flag and
                trading_data.market_order_available_flag
            ):
                if self.is_waiting_open:
                    not self.is_waiting_open = True
                    # logger
                time.sleep(self.wait_time)

            else:
                if self.is_waiting_open:
                    self.is_waiting_open = False
                    # logger
                return

