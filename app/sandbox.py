from tinkoff.invest import MoneyValue
from tinkoff.invest.services import Services
from tinkoff.invest.utils import decimal_to_quotation

from decimal import Decimal

from .logger import Logger

class SandboxManager:
    """ Класс для управления аккаунтами-песочницами """

    def __init__(self, client: Services, money: int = 5000, currency: str = "rub") -> None:
        self.client = client
        self.account_id: str = None 
        self.money_for_add: int = money
        self.currency: str = currency
        self.on_delete: bool = False
        self.logger = Logger()

    def add_money_sandbox(self, currency="rub"):
        """Function to add money to sandbox account."""
        money = decimal_to_quotation(Decimal(self.money_for_add))
        self.logger.info(message=f"SANDBOX_ACC_SETUP [{self.account_id}] >> add money: {self.money_for_add} {self.currency}",
                         module=__name__)
        return self.client.sandbox.sandbox_pay_in(
            account_id=self.account_id,
            amount=MoneyValue(units=money.units, nano=money.nano, currency=currency),
        )

    def close_all_sandbox(self) -> None:
        """ Удаление всех существующий счетов-песочниц """
        sandbox_accounts = self.client.users.get_accounts()
        self.logger.info(message=f"SANDBOX_ACC_SETUP >> close all sandbox accounts",
                         module=__name__)
        for sandbox_account in sandbox_accounts.accounts:
            self.client.sandbox.close_sandbox_account(account_id=sandbox_account.id)

    def open_new_sandbox(self, delete_after_use: bool = False) -> None:
        """
        Открытие нового счета. Возможно открыть счет с пометкой на удаление 
        после завершения работы сервиса (полезен для тестовых запусков при уже запущенном сервисе)
        :param delete_after_use: True - создается счет, который по завершению работы будет удален
        """
        # open new sandbox account
        self.on_delete = delete_after_use
        sandbox_account = self.client.sandbox.open_sandbox_account()
        self.account_id = sandbox_account.account_id
        self.logger.info(message=f"SANDBOX_ACC_SETUP [{self.account_id}] >> new account has been created, ON_DELETE={self.on_delete}",
                         module=__name__)
        self.add_money_sandbox()
    
    def close_current_sandbox(self):
        if self.account_id is None: return
        self.logger.info(message=f"SANDBOX_ACC_SETUP [{self.account_id}] >> close current account",
                         module=__name__)
        self.client.sandbox.close_sandbox_account(account_id=self.account_id)


