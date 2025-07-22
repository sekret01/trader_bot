from datetime import timedelta
from http.client import responses
from typing import Generator

from tinkoff.invest.services import Services

from logger import Logger

from tinkoff.invest import Client, CandleInterval, HistoricCandle
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import now

from set_config import TOKEN


class InfoRequester:
    """ Класс для запроса информации от инвестиций """

    def __init__(self, client: Services, is_sandbox: bool = False):
        self.sandbox_mode = is_sandbox
        self.client: Services = client
        self.target: INVEST_GRPC_API | INVEST_GRPC_API_SANDBOX = INVEST_GRPC_API  # режим обычный\песочница
        self.logger = Logger()

    def get_candles(
            self,
            figi: str,
            days_back: int = 1,
            timeframe: CandleInterval = CandleInterval.CANDLE_INTERVAL_HOUR
    ) -> Generator[HistoricCandle, None, None] | None:
        """
        Получение свечей актива за определенный период
        :param figi: идентификатор figi актива
        :param days_back: количество дней, отсчитываемых для статистики (по умолчанию 1)
        :param timeframe: период построение свечей (по умолчанию 1 час)
        :return: генератор с данными о свечах по заданным параметрам
        """
        response = None
        try:
            self.logger.info(message=f"figi [{figi}] - старт получения свечей [days_back:{days_back}, timeframe:{timeframe}]")
            response = self.client.get_all_candles(
                from_=now() - timedelta(days_back),
                to=now(),
                figi=figi,
                interval=timeframe
            )
        except Exception as ex:
            self.logger.error(message=f"figi [{figi}] - получение свечей завершено с ошибкой: {ex}", module=__name__)
        return response
