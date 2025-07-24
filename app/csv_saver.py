import os
from os import path
import datetime
from typing import Literal
from tinkoff.invest.utils import money_to_decimal
from tinkoff.invest.services import Services


class CSV_Saver:
    """ Класс для сохранения данных в формате csv """

    def __init__(self, client: Services):
        self.market_data_path: str = "reports/market_data.csv"
        self.balance_statistic_path: str = "reports/balance_statistic.csv"
        self.header_market = "date,time,name,figi,signal,operation,amount,price"
        self.header_balance = "date,time,total,etf,shares,bounds,currencies,futures,options,sp"
        self.client: Services = client
        self._check_exists()

    def _check_exists(self):
        """ Функция проверки наличия файлов сохранения данных """

        if not path.exists(self.market_data_path):
            with open(self.market_data_path, 'w', encoding='utf-8') as file:
                file.write(self.header_market + '\n')

        # возможно добавить логику на проверку корректности данных

        if not path.exists(self.balance_statistic_path):
            with open(self.balance_statistic_path, 'w', encoding='utf-8') as file:
                file.write(self.header_balance + '\n')

        # возможно добавить логику на проверку корректности данных

    def write_market_data(
            self,
            name: str,
            figi: str,
            signal: int,
            operation: Literal["SELL", "BUY", "SKIP"],
            price: float,
            amount: int
    ) -> None:
        """ Запись данных об операции в csv """
        with open(self.market_data_path, "a") as file:
            date_now = datetime.datetime.now()
            time_ = f"{date_now.hour}:{date_now.minute}:{date_now.second}"
            file.write(f"{date_now.date()},{time_},{name},{figi},{signal},{operation},{price},{amount}\n")

    def write_balance_data(self):
        """ Запись данных о балансе счета в csv """
        account_id = self.client.users.get_accounts().accounts[0].id
        data = self.client.operations.get_portfolio(account_id=account_id)

        portfolio = float(money_to_decimal(data.total_amount_portfolio))
        etf = float(money_to_decimal(data.total_amount_etf))
        shares = float(money_to_decimal(data.total_amount_shares))
        bounds = float(money_to_decimal(data.total_amount_bonds))
        currencies = float(money_to_decimal(data.total_amount_currencies))
        futures = float(money_to_decimal(data.total_amount_futures))
        options = float(money_to_decimal(data.total_amount_options))
        sp = float(money_to_decimal(data.total_amount_sp))

        with open(self.balance_statistic_path, "a") as file:
            date_now = datetime.datetime.now()
            time_ = f"{date_now.hour}:{date_now.minute}:{date_now.second}"
            file.write(f"{date_now.date()},{time_},{portfolio},{etf},{shares},{bounds},{currencies},{futures},{options},{sp}\n")