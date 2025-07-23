import os
from os import path
import datetime
from typing import Literal


class CSV_Saver:
    """ Класс для сохранения данных в формате csv """

    def __init__(self):
        self.market_data_path: str = "reports/market_data.csv"
        self.operations_data_path: str = "reports/operation_data.csv"
        self.header_market = "date,time,name,figi,operation,price,amount," \
                           "total_price,etf_price,share_price,bounds_price," \
                           "currencies_price,futures_price,options_price,sp_price"
        self.header_operations = "date,time,name,figi,MA_small,MA_long,MA_small_val,MA_long_val,RSI,signal"
        self._check_exists()

    def _check_exists(self):
        """ Функция проверки наличия файлов сохранения данных """

        if not path.exists(self.market_data_path):
            with open(self.market_data_path, 'w', encoding='utf-8') as file:
                file.write(self.header_market + '\n')

        # возможно добавить логику на проверку корректности данных

        if not path.exists(self.operations_data_path):
            with open(self.operations_data_path, 'w', encoding='utf-8') as file:
                file.write(self.header_operations + '\n')

        # возможно добавить логику на проверку корректности данных

    def write_market_data(
            self,
            name: str,
            figi: str,
            operation: Literal["SELL", "BUY"],
            price: float,
            amount: int,
            total_price: float,
            etf_price: float,
            share_price: float,
            bounds_price: float,
            currencies_price: float,
            futures_price: float,
            options_price: float,
            sp_price: float,
    ) -> None:
        """ Запись данных в csv для хранения действий и анализа """
        with open(self.market_data_path, "a") as file:
            date_now = datetime.datetime.now()
            time_ = f"{date_now.hour}:{date_now.minute}:{date_now.second}"
            file.write(f"{date_now.date()},{time_},{name},{figi},{operation},{price},{amount},{total_price},{etf_price},{share_price},{bounds_price},{currencies_price},{futures_price},{options_price},{sp_price}\n")

    def write_operation_data(
            self,
            name: str,
            figi: str,
            MA_small: int,
            MA_long: int,
            MA_small_val: float,
            MA_long_val: float,
            RSI: float,
            signal: int
    ):
        with open(self.operations_data_path, "a") as file:
            date_now = datetime.datetime.now()
            time_ = f"{date_now.hour}:{date_now.minute}:{date_now.second}"
            file.write(f"{date_now.date()},{time_},{name},{figi},{MA_small},{MA_long},{MA_small_val},{MA_long_val},{RSI},{signal}\n")