import time
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
import configparser

from tinkoff.invest import Client, CandleInterval
from tinkoff.invest.utils import now

from app import (
    Strategy,
    TrendFollowing,
)

import warnings
warnings.filterwarnings("ignore")


STRATEGY_TYPE: type = TrendFollowing
DAYS_BACK: int = 30
NAME: str = ""
FIGI: str = ""
INTERVAL: CandleInterval = CandleInterval.CANDLE_INTERVAL_HOUR
BALANCE: int = 0

MA_small: int = 0
MA_long: int = 0

# =====================================================
TIMEFRAMES_LIST: dict[CandleInterval,int] = {
    CandleInterval.CANDLE_INTERVAL_1_MIN: 30,
    CandleInterval.CANDLE_INTERVAL_5_MIN: 30,
    CandleInterval.CANDLE_INTERVAL_30_MIN: 30,
    CandleInterval.CANDLE_INTERVAL_HOUR: 30,
    CandleInterval.CANDLE_INTERVAL_2_HOUR: 120,
    CandleInterval.CANDLE_INTERVAL_4_HOUR: 120,
}
MA_LIST: list[tuple[int,int]] = [
    (5, 10),
    (5, 20),
    (10, 20),
    (20, 50),
    (50, 100),
]
# ======================================================

CSV_PATH = "analysis_pack/results_of_strategy_analysis/test_indicators.csv"

def clear_file():
    with open(CSV_PATH, 'w', encoding='utf8') as file:
        file.write("name;figi;timeframe;days_back;ma_small;ma_long;total_before;total_result;delta\n")

def write_line(data: dict):
    with open(CSV_PATH, 'a', encoding='utf8') as file:
        file.write(f"{data["name"]};{data['figi']};{data['timeframe']};{data['days_back']};{data['ma_small']};" +
                   f"{data['ma_long']};{data['total_before']};{data['total_result']};{data['delta']}\n")

# ======================================================

def get_token() -> str:
    parser = configparser.ConfigParser()
    parser.read("configs/.configs.ini")
    return parser["TOKENS"]["token"]

def market_emulator(df: pd.DataFrame, name: str = "") -> dict[str,float]:
    is_bought = False
    start_price = df.iloc[0]["close"]
    amount = BALANCE // start_price
    total = BALANCE + start_price // 2
    res_total = total
    size = df.shape[0]
    commission_data = {
        "TMOS@": (0, 0.1),
        "AMRE": (0.1, 0.1)
    }

    for i in range(size):
        line = df.iloc[i]
        if line["signal"] == 1 and not is_bought:
            com = commission_data.get(name) or (0, 0)
            res_total -= (line["close"] * amount + line["close"] * com[0] * amount)
            is_bought = True
            # print(f"{line["close"]:^10}|{line["signal"]:^10}|{'BUY':^10}")

        elif line["signal"] == -1 and is_bought:
            com = commission_data.get(name) or (0, 0)
            res_total += (line["close"] * amount - line["close"] * com[1] * amount)
            is_bought = False
            # print(f"{line["close"]:^10}|{line["signal"]:^10}|{'SELL':^10}")

        else:
            # print(f"{line["close"]:^10}|{line["signal"]:^10}|{'SKIP':^10}")
            ...
    if is_bought:
        res_total += df.iloc[size - 1]["close"]

    delta = round((res_total - total) / total * 100, 2)
    print(f"BEFORE: {total}")
    print(f"NOW: {res_total}")
    print(f"DELTA: {delta}%")

    return {"total": total, "res_total": res_total, "delta": delta}


def build_graphic(df: pd.DataFrame) -> None:
    plt.figure(figsize=(16, 8))

    plt.subplot(211)
    plt.plot(df["close"], label="цена закрытия", color='blue')
    plt.plot(df["MA_small"], label="MA_small", linestyle='--', color='orange')
    plt.plot(df["MA_long"], label="MA_long", linestyle='--', color='purple')
    plt.scatter(
        df[df["signal"] == 1].index,
        df[df["signal"] == 1]["close"],
        color='green',
        label="ПОКУПАТЬ"
    )
    plt.scatter(
        df[df["signal"] == -1].index,
        df[df["signal"] == -1]["close"],
        color='red',
        label="ПРОДАВАТЬ"
    )
    plt.legend()
    plt.grid(True)

    plt.subplot(212)
    plt.plot(df["RSI"], label="RSI", color="black")
    plt.legend()
    plt.grid(True)
    plt.show()

# =======================================================

def start_graphic_test() -> None:
    token = get_token()
    with Client(token) as client:

        candles_list = []
        for candle in client.get_all_candles(
            from_=now() - timedelta(days=DAYS_BACK),
            to=now(),
            figi=FIGI,
            interval=INTERVAL
        ):
            candles_list.append(candle)

        strategy: STRATEGY_TYPE = STRATEGY_TYPE(
            MA_small=MA_small,
            MA_long=MA_long,
            asset_info=f"{NAME}:{FIGI}")
        strategy.prepare_data(
            candles=candles_list
        )

        df = strategy.get_all_candles_with_signals()
        # df = df[:600]
        market_emulator(df)
        build_graphic(df)


def start_iterate_test(asset_data: dict[str,str]) -> None:
    token = get_token()
    with Client(token) as client:
        clear_file()

        for name, figi in asset_data.items():
            for timeframe, days_back in TIMEFRAMES_LIST.items():

                candles_list = []

                for candle in client.get_all_candles(
                        from_=now() - timedelta(days=days_back),
                        to=now(),
                        figi=figi,
                        interval=timeframe
                ):
                    candles_list.append(candle)

                for ma_small, ma_long in MA_LIST:

                    strategy: STRATEGY_TYPE = STRATEGY_TYPE(
                        MA_small=ma_small,
                        MA_long=ma_long,
                        asset_info=f"{name}:{figi}")
                    strategy.prepare_data(
                        candles=candles_list
                    )

                    df = strategy.get_all_candles_with_signals()
                    result_data = market_emulator(df, name)
                    # name,figi,timeframe,days_back,ma_small,ma_long,total_before,total_result,delta
                    result_data = {
                        "name": name,
                        "figi": figi,
                        "timeframe": str(timeframe),
                        "days_back": days_back,
                        "ma_small": ma_small,
                        "ma_long": ma_long,
                        "total_before": str(result_data["total"]).replace('.', ','),
                        "total_result": str(result_data["res_total"]).replace('.', ','),
                        "delta": str(result_data["delta"]).replace('.', ',')
                    }

                    write_line(result_data)
                    print(result_data)

                time.sleep(15)



def get_figi():
    token = get_token()
    with Client(token) as client:
        data = client.instruments.find_instrument(query=NAME)
        for instr in data.instruments:
            print(f"{instr.name:<50}|{instr.ticker:^20}|{instr.figi:>17}")


if __name__ == "__main__":

    STRATEGY_TYPE = TrendFollowing
    DAYS_BACK = 60
    NAME = "AMRE"
    FIGI = "TCS10A101X50"
    INTERVAL = CandleInterval.CANDLE_INTERVAL_HOUR
    BALANCE = 10_000

    MA_small: int = 50
    MA_long: int = 100

    asset_data = {
        "TITR@": "TCS30A108BL2",
        "TRUR": "BBG000000001",  # TRUR
        "TGLD": "TCS10A101X50",
        "TRND": "TCS00A10B0G9",
        "TLCB@": "TCS20A107597",
        "TDIV@": "TCS10A107563",
    }

    # start_graphic_test()
    start_iterate_test(asset_data=asset_data)

    # get_figi()
