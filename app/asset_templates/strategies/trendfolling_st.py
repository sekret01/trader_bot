from tinkoff.invest import HistoricCandle
from tinkoff.invest.utils import quotation_to_decimal

from .base_strategy import Strategy
from app import Logger
import pandas as pd


class TrendFollowing(Strategy):
    """ Определение сигнала по стратегии TrendFollowing """

    def __init__(
            self,
            MA_small: int = 9,
            MA_long: int = 15,
            asset_info: str | None = None
    ):
        self.candle_df: pd.DataFrame | None = None
        self.MA_small: int = MA_small
        self.MA_long: int = MA_long
        self.logger: Logger = Logger()
        self.asset_info: str | None = asset_info

    def prepare_data(self, candles: list[HistoricCandle]) -> None:
        """ Подготовка индикаторов для последующего определения сигнала """
        data = {"close": []}
        for candle in candles:
            data["close"].append(float(quotation_to_decimal(candle.close)))

        self.candle_df = pd.DataFrame(data)
        self.candle_df["MA_small"] = self.candle_df["close"].rolling(self.MA_small).mean()
        self.candle_df["MA_long"] = self.candle_df["close"].rolling(self.MA_long).mean()
        self.candle_df["RSI"] = self.calculate_rsi()
        self.logger.info(message=f"{self.asset_info} indicators have been calculated",
                         module=__name__)


    def get_signal(self) -> int:
        """ Функция определения сигнала к покупке, продаже или бездействию по стратегии """
        last_signals = self.candle_df[-1:]
        signal = 0
        if ((last_signals["close"].values[0] > last_signals["MA_small"].values[0])
                and (last_signals["MA_small"].values[0] > last_signals["MA_long"].values[0])
                and last_signals["RSI"].values[0] > 50):
            signal = 1
        if ((last_signals["close"].values[0] < last_signals["MA_small"].values[0])
                # or (last_signals["MA_small"] > last_signals["MA_long"])
                or last_signals["RSI"].values[0] < 50):
            signal = -1

        self.logger.info(
            message=f"{self.asset_info} INDICATORS -> [CLOSE:{last_signals["close"].values[0]} | MA_{self.MA_small}:{last_signals["MA_small"].values[0]} |" \
                    f" MA_{self.MA_long}:{last_signals["MA_long"].values[0]} | RSI:{last_signals["RSI"].values[0]}] >> " \
                    f"SIGNAL:{signal}",
            module=__name__
        )
        return signal


    # dop

    def calculate_rsi(self):
        """ Функция расчета значения RSI для ряда свеч """
        window = 14  # для ETF
        delta = self.candle_df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
