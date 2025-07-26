from datetime import timedelta
from typing import Literal

from ..logger import Logger
from .strategies import Strategy
from .asset_template import AssetTemplate
from ..csv_saver import CSV_Saver

from tinkoff.invest import CandleInterval, InstrumentType, HistoricCandle, AioRequestError, OrderType, OrderDirection
from tinkoff.invest.services import Services
from tinkoff.invest.utils import now, quotation_to_decimal, money_to_decimal

import time



class CandleTemplate(AssetTemplate):
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
        self.account_id: int | None = None
        self.figi: str = figi
        self.name: str = name
        self.amount: int = amount
        self.days_back: int = days_back
        self.timeframe: CandleInterval = timeframe
        self.check_interval: int = check_interval
        self.type_: InstrumentType = type_
        self.strategy: Strategy = strategy
        self.logger: Logger = Logger()

        self.candles: list[HistoricCandle] = []
        self.is_bought: bool = False
        self.is_waiting_open: bool = False
        self.wait_time: int = 60 * 10
        self.saver: CSV_Saver | None = None

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
        if self.account_id is None:
            self.account_id = self.client.users.get_accounts().accounts[0].id
        self.saver = CSV_Saver(self.client)
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
            post_order_response = self.client.orders.post_order(
                figi=self.figi,
                quantity=self.amount,
                account_id=self.account_id,
                order_type=OrderType.ORDER_TYPE_MARKET,
                direction=OrderDirection.ORDER_DIRECTION_BUY
            )
            self.is_bought = True
            self.logger.info(message=f"{self.__repr__()} action:BUY amount:{self.amount} "
                                     f"price:{float(quotation_to_decimal(post_order_response.initial_order_price))}",
                             module=__name__)
            price = float(quotation_to_decimal(post_order_response.initial_order_price))
            operation = "BUY"

        elif signal == -1 and self.is_bought:
            post_order_response = self.client.orders.post_order(
                figi=self.figi,
                quantity=self.amount,
                account_id=self.account_id,
                order_type=OrderType.ORDER_TYPE_MARKET,
                direction=OrderDirection.ORDER_DIRECTION_SELL
            )
            self.is_bought = False
            self.logger.info(message=f"{self.__repr__()} action:SELL amount:{self.amount} "
                                     f"price:{float(quotation_to_decimal(post_order_response.initial_order_price))}",
                             module=__name__)
            price = float(quotation_to_decimal(post_order_response.initial_order_price))
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

