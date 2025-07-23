import os
import brush
from console_menu import ConsoleMenu
from info_requester import InfoRequester

class Console:
    """ Класс, отвечающий за вывод данных """

    def __init__(self):
        self.command: tuple[int, str] = (-1, "")
        self.is_active: bool = False

    def get_command(self) -> tuple[int, str] | None:
        if self.is_active:
            self.is_active = False
            return self.command
        return None

    # MENUS

    def show_main_menu(self):
        """ Главное меню программы, при входе """
        commands = [
            "запуск (песочница)",
            "режим песочница",
            "выход"
        ]
        menu = ConsoleMenu(commands=commands)
        self.command = menu.get_command()
        self.is_active = True

    def show_working_menu(self):
        """ Меню, открывающееся после запуска бота """
        commands = [
            "просмотр кошелька",
            "просмотр логов",
            "завершение работы"
        ]
        menu = ConsoleMenu(commands=commands)
        self.command = menu.get_command()
        self.is_active = True


