from datetime import timedelta
from typing import Generator

from tinkoff.invest.sandbox.client import SandboxClient

from logger import Logger
from set_config import SANDBOX_TOKEN

from tinkoff.invest import MoneyValue, Client, CandleInterval, HistoricCandle, InstrumentType
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import now
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal
from decimal import Decimal
from strategy_trendfolling import TrendFolling
from asset import Asset

"""
TITR@ - TCS30A108BL2  (6.5 rub)
"""

INTERVAL: CandleInterval
CHECK_INTERVAL: int
AMOUNT: int
DAYS_BACK: int
ASSETS_DATA: list[dict]

def create_sandbox():
    ...

def add_money_sandbox(client, account_id, money, currency="rub"):
    """Function to add money to sandbox account."""
    money = decimal_to_quotation(Decimal(money))
    return client.sandbox.sandbox_pay_in(
        account_id=account_id,
        amount=MoneyValue(units=money.units, nano=money.nano, currency=currency),
    )

def create_assets_list(asset_data: list[dict]) -> list[Asset]:
    result = []
    for asset in asset_data:
        result.append(Asset(
            figi=asset["figi"],
            amount=asset["amount"],
            type_=asset["type_"],
            name=asset["name"]
        ))
    return result


def main():

    with SandboxClient(SANDBOX_TOKEN) as client:
        sandbox_accounts = client.users.get_accounts()
        print(f"количество аккаунтов: {len(sandbox_accounts.accounts)}")

        # close all sandbox accounts
        for sandbox_account in sandbox_accounts.accounts:
            client.sandbox.close_sandbox_account(account_id=sandbox_account.id)

        # open new sandbox account
        sandbox_account = client.sandbox.open_sandbox_account()
        print(sandbox_account.account_id)

        account_id = sandbox_account.account_id

        print(add_money_sandbox(client=client, account_id=account_id, money=TOTAL_SUMMA))
        print("money: ", float(quotation_to_decimal(client.operations.get_positions(account_id=account_id).money[0])))
        assets_list = create_assets_list(asset_data=ASSETS_DATA)

        strategy = TrendFolling(
            days_back=DAYS_BACK,
            timeframe=INTERVAL,
            check_interval=CHECK_INTERVAL,
            client=client,
            assets=assets_list
        )

        strategy.start()




if __name__ == "__main__":
    # ===================================================
    INTERVAL = CandleInterval.CANDLE_INTERVAL_HOUR
    ASSETS_DATA = [
        {
            "name": "TITR@",  # 6.5
            "figi": "TCS30A108BL2",
            "amount": 160,
            "type_": InstrumentType.INSTRUMENT_TYPE_ETF
        },
        {
            "name": "TRUR",  # 9.08
            "figi": "BBG000000001",
            "amount": 110,
            "type_": InstrumentType.INSTRUMENT_TYPE_ETF
        },
        {
            "name": "TGLD",  # 10.5
            "figi": "TCS10A101X50",
            "amount": 100,
            "type_": InstrumentType.INSTRUMENT_TYPE_ETF
        },
        {
            "name": "TRND",  # 9.58
            "figi": "TCS00A10B0G9",
            "amount": 110,
            "type_": InstrumentType.INSTRUMENT_TYPE_ETF
        },
    ]
    DAYS_BACK = 30
    CHECK_INTERVAL = 1 * 60 * 60
    TOTAL_SUMMA = 5000
    # ===================================================

    main()