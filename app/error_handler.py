from __future__ import annotations


class ErrorHandler:
    """
    Класс для перенаправления сообщений об ошибках.
    Использует список обработчиклв-функций, которые 
    принимают в качестве аргумента msg - строку сообщения.
    """

    _instance: ErrorHandler = None
    handlers: list[callable] = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
        return cls._instance
        
    # @staticmethod
    def add_handler(self, func: callable) -> None:
        """
        Функция добаления обработчика ошибок
        :param func: функция для обработки ошибок. Должна иметь входной параметр func(msg: str) -> None
        """
        self.handlers.append(func)
    
    # @staticmethod
    def error(self, msg: str) -> None:
        """ Активация обработчиков ошибок """
        for handler in self.handlers:
            try:
                handler(msg=msg)
            except Exception as ex:
                pass
