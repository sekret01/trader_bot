from __future__ import annotations
import logging
import datetime

logging.basicConfig(filename="logs.log", format="<%(asctime)s> %(levelname)s: %(message)s", level=logging.INFO)


class Logger:
    """ Логирование в файл, возможен вывод в консоль при stream_out=True """
    _instance: Logger | None = None
    logger: logging.Logger = logging.getLogger("main logger")
    stream_out: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance


    def info(self, message: str, module: str = ""):
        self.logger.info(module + " > " + message if module else message)
        if self.stream_out:
            print(f"[{datetime.datetime.now().date()}] --INFO-- [{module}]: {message}")

    def error(self, message: str, module: str = ""):
        self.logger.error(module + " > " + message if module else message)
        if self.stream_out:
            print(f"[{datetime.datetime.now().date()}] !!-ERROR-!! [{module}]: {message}")

    def warning(self, message: str, module: str = ""):
        self.logger.warning(module + " > " + message if module else message)
        if self.stream_out:
            print(f"[{datetime.datetime.now().date()}] <-WARNING-> [{module}]: {message}")