from __future__ import annotations
import json


class MessageSteck:
    """
    Класс для записи в файл сообщений,
    идущих из разных потоков
    """
    _instance: MessageSteck = None
    _queue: list[dict] = []
    is_active: bool = False
    write_path: str = ""

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MessageSteck, cls).__new__(cls)
        return cls._instance


    def put_message(self, message: dict) -> None:
        """ Функция для упаковки сообщения в очередь сообщений """
        self._queue.append(message)
        if self.is_active:
            return
        self.is_active = True
        self._write_data()

    def _write_data(self) -> None:
        """ Запись данных из очереди сообщений """
        with open(self.write_path, 'r', encoding='utf-8') as file:
            old_data: dict = json.load(file)

        while len(self._queue) > 0:
            asset_data = self._queue.pop(0)
            old_data[asset_data["figi"]] = asset_data

        with open(self.write_path, 'w', encoding='utf-8') as file:
            json.dump(old_data, file)

