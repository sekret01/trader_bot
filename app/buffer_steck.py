from __future__ import annotations
from pathlib import Path
import datetime
import configparser
from .logger import Logger


def get_last_date() -> datetime.datetime.date:
    """ Просмотр последней сохраненной даты """
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read("configs/start_app.ini")
    try:
        str_date = cfg_parser["WORK"]["last_date"]
        date = datetime.datetime.strptime(str_date, "%Y-%m-%d").date()
        
    except Exception as ex:
        Logger().error(message="Last date has been not found", module=__name__)
        date = datetime.datetime.now().date()
    return date

def save_new_last_data(date: datetime.datetime.date) -> None:
    """ Сохранение новой последней даты """
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read("configs/start_app.ini")
    cfg_parser["WORK"]["last_date"] = str(date)
    with open("configs/start_app.ini", "w", encoding='utf-8') as file:
        cfg_parser.write(file)


class BufferSteck:
    """
    Класс для записи данных в буфер
    """
    _instance: BufferSteck = None
    _queue: list[dict] = []
    is_active: bool = False
    buffer_folder: str = Path("app/buff")
    last_date: datetime.date = get_last_date()

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
            date_now = datetime.datetime.now().date()
            if date_now != self.last_date:
                self._clear_file(file_path)
                self.last_date = date_now
                save_new_last_data(date=date_now)
            
            self._check_file(file_path)
            msg = buff_data["message"]

            with file_path.open(mode='a', encoding='utf-8') as file:
                file.write(msg + '\n')

        self.is_active = False

    def _check_file(self, file_path: str) -> None:
        """ Проверка существования файла сохранения и правильности его данных """
        if not file_path.exists():
            file_path.touch()
    
    def _clear_file(self, file_path: Path) -> None:
        """ Очистка данных буффера по окончанию срока хранения """
        file_path.write_text("")


