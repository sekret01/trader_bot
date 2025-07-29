from __future__ import annotations
import json
from os import path

from .logger import Logger

class MessageSteck:
    """
    Класс для записи в файл сообщений,
    идущих из разных потоков
    """
    _instance: MessageSteck = None
    _queue: list[dict] = []
    is_active: bool = False
    write_path: str = "configs/status_save.json"  # возможно положить в app
    logger = Logger()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MessageSteck, cls).__new__(cls)
        return cls._instance


    def put_message(self, message: dict) -> None:
        """ Функция для упаковки сообщения в очередь сообщений """
        self._queue.append(message)
        self.logger.info(message=f"status from [{message.get("name")}:{message.get("figi")}] accepted", module=__name__)
        if self.is_active:
            return
        self.is_active = True
        self._write_data()

    def _write_data(self) -> None:
        """ Запись данных из очереди сообщений """
        self._check_file()
        with open(self.write_path, 'r', encoding='utf-8') as file:
            old_data: dict = json.load(file)

        while len(self._queue) > 0:
            asset_data = self._queue.pop(0)
            old_data[asset_data["figi"]] = asset_data

        with open(self.write_path, 'w', encoding='utf-8') as file:
            json.dump(old_data, file)

        self.is_active = False

    def _check_file(self) -> None:
        """ Проверка существования файла сохранения и правильности его данных """

        def create_file():
            """ Создание файла """
            with open(self.write_path, 'w', encoding='utf-8') as correct_file:
                correct_file.write('')
                json.dump(dict(), correct_file)

            self.logger.warning(message="data was incorrect > new status-file created", module=__name__)
            return


        if not path.exists(self.write_path):
            create_file()

        with open(self.write_path, 'r', encoding='utf-8') as file:
            write_data = json.load(file)
            if type(write_data) != dict:
                create_file()

