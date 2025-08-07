from __future__ import annotations
from pathlib import Path


class BufferSteck:
    """
    Класс для записи данных в буфер
    """
    _instance: BufferSteck = None
    _queue: list[dict] = []
    is_active: bool = False
    buffer_folder: str = Path("app/buff")  # возможно положить в app

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BufferSteck, cls).__new__(cls)
        return cls._instance


    def put_message(self, file_n: str, message: dict) -> None:
        """ Функция для упаковки сообщения в очередь сообщений """
        self._queue.append({"file": file_n, "message": message})
        if self.is_active:
            return
        self.is_active = True
        self._write_data()

    def _write_data(self) -> None:
        """ Запись данных из очереди сообщений """
        while len(self._queue) > 0:
            buff_data = self._queue.pop(0)
            file_path: Path = self.buffer_folder / buff_data["file"]
            self._check_file(file_path)
            msg = buff_data["message"]

            with file_path.open(mode='a', encoding='utf-8') as file:
                file.write(msg + '\n')

        self.is_active = False

    def _check_file(self, file_path: str) -> None:
        """ Проверка существования файла сохранения и правильности его данных """
        if not file_path.exists():
            file_path.touch()

