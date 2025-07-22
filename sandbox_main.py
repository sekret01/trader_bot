from datetime import timedelta
from typing import Generator

from tinkoff.invest.sandbox.client import SandboxClient

from logger import Logger
from set_config import SANDBOX_TOKEN

from tinkoff.invest import MoneyValue, Client, CandleInterval, HistoricCandle
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import now
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal
from decimal import Decimal
from strategy_trendfolling import TrendFolling

"""
TITR@ - TCS30A108BL2  (6.5 rub)
"""

INTERVAL: CandleInterval
CHECK_INTERVAL: int
AMOUNT: int
DAYS_BACK: int
FIGI: str

def create_sandbox():
    ...

def add_money_sandbox(client, account_id, money, currency="rub"):
    """Function to add money to sandbox account."""
    money = decimal_to_quotation(Decimal(money))
    return client.sandbox.sandbox_pay_in(
        account_id=account_id,
        amount=MoneyValue(units=money.units, nano=money.nano, currency=currency),
    )


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

        strategy = TrendFolling(
            figi=FIGI,
            days_back=DAYS_BACK,
            timeframe=INTERVAL,
            check_interval=CHECK_INTERVAL,
            client=client,
            amount=AMOUNT
        )

        strategy.start()




if __name__ == "__main__":
    # ===================================================
    INTERVAL = CandleInterval.CANDLE_INTERVAL_HOUR
    FIGI = "TCS30A108BL2"
    DAYS_BACK = 30
    CHECK_INTERVAL = 60 * 60
    AMOUNT = 750
    TOTAL_SUMMA = 5000
    # ===================================================

    main()