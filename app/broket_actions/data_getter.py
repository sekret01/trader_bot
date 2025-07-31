from datetime import datetime
from typing import Generator

from tinkoff.invest import CandleInterval, HistoricCandle
from tinkoff.invest.services import Services
from tinkoff.invest.utils import now


class TinkoffDataGetter:
    """ Класс для запросов информации """

    def __init__(self, client: Services) -> None:
        self.client = client

    def get_candles(
            self,
            figi: str,
            interval: CandleInterval,
            from_: datetime,
            to: datetime = now()
    ) ->  Generator[HistoricCandle, None, None]:
        """
        Получение свечей за определенный период по определенному активу
        :param figi: figi индикатор актива
        :param interval: интервал свечей
        :param from_: с какого периода свечи
        :param to: до какого периода свечи
        """

        return self.client.get_all_candles(
            figi=figi,
            interval=interval,
            from_=from_,
            to=to
        )