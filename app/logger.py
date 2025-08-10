from __future__ import annotations
import logging
import datetime

logging.basicConfig(filename="app/logs/main_logs.log", format="<%(asctime)s> %(name)s %(levelname)s: %(message)s", level=logging.INFO)

# отключение логгера от tinkoff.invest
tinkoff_logger = logging.getLogger("tinkoff.invest.logging")
tinkoff_logger.setLevel(logging.ERROR)


class Logger:
    """ Логирование в файл, возможен вывод в консоль при stream_out=True """
    _instance: Logger | None = None
    logger: logging.Logger = logging.getLogger("MAIN")
    stream_out: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance


    def get_time(self, date: datetime.datetime) -> str:
        return f"{date.hour}:{date.minute}:{date.second}"

    def info(self, message: str, module: str):
        self.logger.info(module + " > " + message if module else message)
        if self.stream_out:
            print(f"[{datetime.datetime.now().date()}  {self.get_time(datetime.datetime.now())}] --INFO-- [{module}]: {message}")

    def error(self, message: str, module: str):
        self.logger.error(module + " > " + message if module else message)
        if self.stream_out:
            print(f"[{datetime.datetime.now().date()}  {self.get_time(datetime.datetime.now())}] !!-ERROR-!! [{module}]: {message}")

    def warning(self, message: str, module: str):
        self.logger.warning(module + " > " + message if module else message)
        if self.stream_out:
            print(f"[{datetime.datetime.now().date()}  {self.get_time(datetime.datetime.now())}] <-WARNING-> [{module}]: {message}")