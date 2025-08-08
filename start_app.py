"""
  Запуск программы осуществляется по настройкам конфигураций,
  все конфигурации необходимо изменять вручную.
  Конфигурации для запуска лежат по пути: configs/start_app.ini

  После запуска программы через этот файл бот начнет работать
  без вывода данных в консоль. Управление так же будет невозможно
  через консоль (только вызов <KeyboardInterrupt> для принудительного
  завершения. Не рекомендуется при стандартном клиенте, так как возможна
  потеря данных).
"""


import configparser
from decimal import Decimal

from tinkoff.invest import Client, MoneyValue
from tinkoff.invest.services import Services
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.utils import decimal_to_quotation

from app import ControlHub
from app import Logger
from app import SandboxManager


_start_config_path = "configs/start_app.ini"
_token_konfig_path = "configs/.configs.ini"
PARSER = configparser.ConfigParser()
LOGGER = Logger()
SANDBOX_MANAGER: SandboxManager = None


def get_configs() -> dict:
    """ Получение конфигураций для настройки и запуска программы """
    parser = configparser.ConfigParser()
    parser.read(_start_config_path)

    configs = dict()
    configs["client_type"] = parser["START_PARAMETERS"]["client_type"]
    configs["check_save"] = parser["START_PARAMETERS"]["check_save"]
    configs["once_test_sandbox"] = parser["START_PARAMETERS"]["once_test_sandbox"]

    return configs

def get_connect_data(configs: dict) -> tuple[type[Client], str] | None:
    """ Установка типа клиента и токена для клиента из конфигурации (стандарт или песочница) """
    PARSER.read(_token_konfig_path)

    if configs["client_type"] == "standard":
        LOGGER.info(message=f"client type for start: [standard]", module=__name__)
        return Client, PARSER["TOKENS"]["token"]

    elif configs["client_type"] == "sandbox":
        LOGGER.info(message=f"client type for start: [sandbox]", module=__name__)
        return SandboxClient, PARSER["TOKENS"]["sandbox"]
    else :
        LOGGER.error(message=f"NOT FOUND client type for start: [{configs["client_type"]}]. Stop launch", module=__name__)
        return None

# def add_money_sandbox(client, account_id, money, currency="rub"):
#     """Function to add money to sandbox account."""
#     money = decimal_to_quotation(Decimal(money))
#     return client.sandbox.sandbox_pay_in(
#         account_id=account_id,
#         amount=MoneyValue(units=money.units, nano=money.nano, currency=currency),
#     )

# def create_sandbox_account(client: Services):
#     sandbox_accounts = client.users.get_accounts()
#     for sandbox_account in sandbox_accounts.accounts:
#         client.sandbox.close_sandbox_account(account_id=sandbox_account.id)

#     # open new sandbox account
#     sandbox_account = client.sandbox.open_sandbox_account()
#     account_id = sandbox_account.account_id
#     add_money_sandbox(client=client, account_id=account_id, money=5000)


def loop():
    while True:
        input()

def main():
    LOGGER.info(message="LAUNCH <start_app> FOR AUTO START BOT", module=__name__)

    configs = get_configs()
    res = get_connect_data(configs)
    if res is None:
        return

    client_type, token = res
    with client_type(token=token) as client:
        account_id = ""
        if client_type == SandboxClient:
            SANDBOX_MANAGER = SandboxManager(client)
            SANDBOX_MANAGER.open_new_sandbox(delete_after_use=configs["once_test_sandbox"] == "1")
            # SANDBOX_MANAGER.add_money_sandbox()  # делается уже в open_new_sandbox
            account_id = SANDBOX_MANAGER.account_id
            # create_sandbox_account(client)
        else:
            account_id = client.users.get_accounts().accounts[0].id  # расчет на то что токен для одного счета
        control_hub = ControlHub(client, account_id)

        # активы собираются либо по листу конфигураций,
        # либо по последним сохраненным статусам
        if configs["check_save"] == '0':
            LOGGER.info(message="Data will be load from configs", module=__name__)
            control_hub.set_strategies()
        elif configs["check_save"] == '1':
            LOGGER.info(message="Data will be load from save_status file", module=__name__)
            # добавить метод для сборки данных из файла сохранения
            ...
        else:
            LOGGER.error(message=f"VALUE ERROR :: <check_save> must be in: [0, 1]. Have: [{configs["check_save"]}]. Stop launch", module=__name__)
            return

        LOGGER.info(message="start strategy", module=__name__)
        control_hub.run_strategies()
        print("Начало работы")

        try:
            loop()
        except KeyboardInterrupt:
            print("Принудительное завершение программы...")
            LOGGER.warning(message="forced program termination", module=__name__)
        except Exception as ex:
            LOGGER.error(message=f"CRITICAL ERROR :: {ex}", module=__name__)

        if (not SANDBOX_MANAGER is None) and (SANDBOX_MANAGER.on_delete):
            SANDBOX_MANAGER.close_current_sandbox()

        control_hub.stop_strategies()
        return

if __name__ == "__main__":
    main()

