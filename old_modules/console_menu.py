import msvcrt
import os


class ConsoleMenu:
    """ Консольный вывод меню """
    
    def __init__(self, commands: list[str] = None) -> None:
        self._commands: list[str] = commands if commands else []
        self._selected = 0
        self.min_len = 20
        os.system('')
        self._process_commands()
    
    def _process_commands(self) -> None:
        """ Добавление пробелов в строки для выравнивания при выводе """
        max_len: int = 0
        for el in self._commands:
            if len(el) > max_len:
                max_len = len(el)
        
        if max_len < self.min_len:
            max_len = self.min_len
        else: max_len += 2
        
        for i in range(len(self._commands)):
            self._commands[i] = f"{self._commands[i]:^{max_len}}"
            
    
    def _draw(self) -> None:
        """ Отрисовка меню с выбранным элементом """
        
        os.system("cls")
        for i, el in enumerate(self._commands):
            if i == self._selected:
                print(f"\033[30;47m{el}\033[0m")
            else:
                print(f"\033[37m{el}\033[0m")
    
    def set_command_list(self, commands: list[str]) -> None:
        """ Назначение списка команд """
        self._commands = commands
    
    def get_command(self) -> tuple[int, str]:
        """ 
        Цикл с отрисовкой меню для выбора команды.
        Команды переключаются нажатием клавиш "вверх" и "вниз",
        ввод - "enter" или "пробел"
        :return: кортеж значений (номер_команды, текст команды)
        """
        redraw: bool = True
        while True:
            if redraw:
                self._draw()
                redraw = False
            
            inp = msvcrt.getch()
            if inp in (b'\r', b' '):
                return self._selected, self._commands[self._selected].strip()
                
            if inp != b'\xe0':
                continue
            
            inp = msvcrt.getch()
            if inp == b'H':
                if (self._selected > 0):
                    self._selected -= 1
                    redraw = True
                    continue
            if inp == b'P':
                if self._selected < len(self._commands) - 1:
                    self._selected += 1
                    redraw = True
                    continue
      
        
