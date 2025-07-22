from typing import Optional

from tinkoff.invest import HistoricCandle, InstrumentType


class Asset:
    """ Класс для хранения данных об активе """

    def __init__(
            self,
            figi: str,
            type_: Optional[InstrumentType] = None,
            name: Optional[str] = ""
    ):
        self.name: str = name
        self.figi: str = figi
        self.type_: InstrumentType | None = type_
        self.candles: list[HistoricCandle] = []
        self.is_bought: bool = False
