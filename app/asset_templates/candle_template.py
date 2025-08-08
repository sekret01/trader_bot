from __future__ import annotations

import datetime
from datetime import timedelta
from typing import Literal

from .strategies import TrendFollowing
from ..logger import Logger
from .strategies import Strategy
from ._asset_template import AssetTemplate
from ..csv_saver import CSV_Saver
from ..status_saver import MessageSteck
from ..buffer_steck import BufferSteck
from ..broker_actions import TinkoffMarketOperations

from tinkoff.invest import CandleInterval, InstrumentType, HistoricCandle, AioRequestError, OrderType, OrderDirection
from tinkoff.invest.services import Services
from tinkoff.invest.utils import now, quotation_to_decimal, money_to_decimal

import time



class CandleTemplate(AssetTemplate):
    """ Шаблон объекта актива, стратегия которого основана на получении данных свечей """

    def __init__(
            self,
            client: Services,
            account_id: str,
            figi: str,
            name: str,
            amount: int,
            days_back: int,
            timeframe: CandleInterval,
            check_interval: int,
            type_: InstrumentType,
            strategy: Strategy
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
        super().__init__()
        self.client: Services = client
        self.account_id: str = account_id
        self.figi: str = figi
        self.name: str = name
        self.amount: int = amount
        self.days_back: int = days_back
        self.timeframe: CandleInterval = timeframe
        self.check_interval: int = check_interval
        self.type_: InstrumentType = type_
        self.strategy: Strategy = strategy

        self.logger: Logger = Logger()
        self.status_saver = MessageSteck()
        self.buffer_steck = BufferSteck()

        self.candles: list[HistoricCandle] = []
        # self.operations_buff: list = []
        self.is_bought: bool = False
        self.is_waiting_open: bool = False
        self.wait_time: int = 60 * 10
        self.saver: CSV_Saver | None = None
        self.operation_controller = TinkoffMarketOperations(self.client, account_id=account_id)

        self._stop: bool = False

    def __repr__(self) -> str:
        return f"{self.name}:[figi={self.figi}]"

    def full_info(self) -> str:
        """ Подробная информация об активе """
        return (f"{self.__repr__()} >> amount:{self.amount}, days_back:{self.days_back}, " +
                f"check_interval:{self.check_interval} (timeframe=CandleInterval({self.timeframe})) "
                f"strategy: {self.strategy.__repr__()}")

    def run(self) -> None:
        """ Подготовка данных и запуск главного цикла """
        # if self.account_id is None:
        #     self.account_id = self.client.users.get_accounts().accounts[0].id
        self.saver = CSV_Saver(self.client, self.account_id)
        self._stop = False
        self.main_loop()

    def stop(self) -> None:
        """ Остановка мониторинга """
        self._stop = True

    def main_loop(self) -> None:
        """ Главный цикл мониторинга актива """
        while True:
            if self._stop: break

            try:
                self.wait_for_open_market()
                self.get_historic_candles()

                self.strategy.prepare_data(candles=self.candles)
                signal = self.strategy.get_signal()
                self.logger.info(message=f"{self.__repr__()} candle data processed", module=__name__)
                self.action(signal)

            except AioRequestError as ex:
                self.logger.error(message=f"{self.__repr__()} stop processing candle data: {ex}", module=__name__)

            time.sleep(self.check_interval)


    def action(self, signal: int) -> None:
        """ Принятие решение на основе сигнала """
        # вынести функции в отдельный класс
        price = 0
        operation: Literal["BUY", "SKIP", "SELL"] = "SKIP"

        if signal == 1 and not self.is_bought:
            post_order_response = self.operation_controller.buy_asset(self.figi, self.amount)
            self.is_bought = True
            self.logger.info(message=f"{self.__repr__()} action:BUY amount:{self.amount} "
                                     f"price:{float(money_to_decimal(post_order_response.initial_order_price))}",
                             module=__name__)
            price = float(money_to_decimal(post_order_response.initial_order_price))
            operation = "BUY"

        elif signal == -1 and self.is_bought:
            post_order_response = self.operation_controller.sell_asset(self.figi, self.amount)
            self.is_bought = False
            self.logger.info(message=f"{self.__repr__()} action:SELL amount:{self.amount} "
                                     f"price:{float(money_to_decimal(post_order_response.initial_order_price))}",
                             module=__name__)
            price = float(money_to_decimal(post_order_response.initial_order_price))
            operation = "SELL"

        else:
            self.logger.info(message=f"{self.__repr__()} action:SKIP",
                             module=__name__)

        self.saver.write_market_data(
            name=self.name,
            figi=self.figi,
            signal=signal,
            operation=operation,
            price=price,
            amount=self.amount
        )
        self.saver.write_balance_data(
            name=self.name,
            figi=self.figi
        )
        self.status_saver.put_message(message=self.to_json())
        _time = datetime.datetime.now().time()
        self.buffer_steck.put_message(
            file_n="operations",
            message=f"<{_time.hour}:{_time.minute}:{_time.second}> [{self.name}] >> {operation} | {round(price, 2)}")

    # def put_operation_in_buff(self, operation_type: Literal["BUY", "SELL"], price: float) -> None:
    #     _time = datetime.datetime.now().time()
    #     operation_string = f"[<{_time}> [{self.name}] >> {operation_type} | {round(price, 2)}"

    def get_historic_candles(self) -> None:
        """ Получение свечей по заданным параметрам """
        self.logger.info(message=f"{self.__repr__()} start getting candles",
                         module=__name__)
        i = 0
        for candle in self.client.get_all_candles(
            from_=now() - timedelta(days=self.days_back),
            to=now(),
            figi=self.figi,
            interval=self.timeframe
        ):
            if not candle in self.candles:
                # if candle.is_complete:
                self.candles.append(candle)
                i += 1
        self.logger.info(message=f"{self.__repr__()} candles got:{i}", module=__name__)

    def wait_for_open_market(self):
        """ Ожидание открытия торгов, если они недоступны """
        while True:
            trading_data = self.client.market_data.get_trading_status(figi=self.figi)

            if not (
                trading_data.api_trade_available_flag and
                trading_data.market_order_available_flag
            ):
                if not self.is_waiting_open:
                    self.is_waiting_open = True
                    self.logger.info(message=f"{self.name}:[{self.figi}] market close", module=__name__)
                time.sleep(self.wait_time)

            else:
                if self.is_waiting_open:
                    self.is_waiting_open = False
                    self.logger.info(message=f"{self.name}:[{self.figi}] market open", module=__name__)
                return


    def to_json(self) -> dict:
        """ Преобразование объекта в json """
        return {
            "account_id": self.account_id,
            "figi": self.figi,
            "name": self.name,
            "amount": self.amount,
            "days_back": self.days_back,
            "timeframe": self.timeframe,
            "check_interval": self.check_interval,
            "type_": self.type_,
            "strategy": self.strategy.to_json(),
            # "candles": self.candles,
            "is_bought": self.is_bought,
            "is_waiting_open": self.is_waiting_open,
            "wait_time": self.wait_time,
            "_stop": self._stop
        }

    @staticmethod
    def from_json(data: dict, client: Services) -> CandleTemplate:
        """ Преобразование json в объект CandleTemplate """
        asset = CandleTemplate(
            client=client,
            figi=data["figi"],
            name=data["name"],
            amount=data["amount"],
            days_back=data["days_back"],
            timeframe=data["timeframe"],
            check_interval=data["check_interval"],
            type_=data["type_"],
            strategy=TrendFollowing.from_json(data["strategy"]),  # ИЗМЕНИТЬ НА АВТООПРЕДЕЛЕНИЕ СТРАТЕГИИ
        )

        asset.account_id = data["account_id"]
        asset.is_bought = data["is_bought"]
        asset.is_waiting_open = data["is_waiting_open"]
        asset.wait_time = data["wait_time"]
        asset._stop = data["_stop"]
        asset.logger = Logger()
        asset.saver = CSV_Saver(client)

        return asset
