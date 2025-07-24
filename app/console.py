import os

from tinkoff.invest import Client
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.services import Services
import configparser

from .visual import ConsoleMenu
from .control_hub import ControlHub
from .logger import Logger


class Console:
    """ Класс для консольного управления работой программы """

    def __init__(self) -> None:
        self.menu_builder = ConsoleMenu()
        self.commands: dict[str,callable] | None = None
        self.control_hub: ControlHub | None = None
        self.client: Services | None = None
        self.token: str = ""
        self.client_type: type(Client) | type(SandboxClient) | None = None
        self.logger: Logger = Logger()
        self.parser = configparser.ConfigParser()
        self.token_konfig_path = "configs/.configs.ini"
        self.loop_menu: bool = True  # тестовая штука

    def run(self) -> None:
        """ Запуск консоли """
        self.logger.info(message=f"START PROGRAM", module=__name__)
        self.show_main_menu()

    def exit(self) -> None:
        """ Выход из программы """
        self.logger.info(message=f"EXIT PROGRAM", module=__name__)
        self.stop_loop_menu()
        os.system('cls')
        print("завершение работы программы...")
        return

    def stop_loop_menu(self) -> None:
        """ Прекращение цикла в меню консоли """
        self.loop_menu = False

    def connect_account(self) -> None:
        """ Подключение к реальному счету """
        self.parser.read(self.token_konfig_path)
        self.token = self.parser["TOKENS"]["token"]
        self.client_type = Client
        self.show_working_menu()

    def connect_sandbox_account(self) -> None:
        """ Подключение к аккаунту-песочнице """
        self.parser.read(self.token_konfig_path)
        self.token = self.parser["TOKENS"]["sandbox"]
        self.client_type = SandboxClient
        self.show_working_menu()


    def show_main_menu(self) -> None:
        """ Главное меню программы """
        while self.loop_menu:
            self.commands = {
                "запуск": print,  # пока на тестировании  -> self.connect_account()
                "запуск [песочница]": self.connect_sandbox_account,
                "выход": self.exit
            }
            self.menu_builder.set_command_list(list(self.commands.keys()))
            result = self.menu_builder.get_command()[1]
            self.commands[result]()
            if not self.loop_menu:
                self.loop_menu = True
                return

    def show_working_menu(self) -> None:
        """ Меню во время работы бота """
        with self.client_type(self.token) as client:
            self.client = client

            self.control_hub = ControlHub(client=self.client)
            self.control_hub.set_strategies()
            self.control_hub.run_strategies()

            while self.loop_menu:
                self.commands = {
                    "вывод логов": self.logs_out_stream,
                    "проверить баланс": print,
                    "остановить": self.stop_loop_menu
                }
                self.menu_builder.set_command_list(list(self.commands.keys()))
                result = self.menu_builder.get_command()[1]
                self.commands[result]()
                if not self.loop_menu:
                    self.loop_menu = True
                    return

    def logs_out_stream(self):
        os.system('cls')
        self.logger.stream_out = True
        input()
        self.logger.stream_out = False
