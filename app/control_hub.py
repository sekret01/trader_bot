from typing import Literal, Optional
import threading
import json
import configparser

from tinkoff.invest import Client, AioRequestError, InstrumentType, CandleInterval
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.services import Services, SandboxService
from tinkoff.invest.utils import quotation_to_decimal

from . import Strategy
from .asset_templates import AssetTemplate, CandleTemplate
from .logger import Logger
from .assets_constructor import AssetsConstructor
from .broker_actions import TinkoffDataGetter


class ControlHub:
    """ Класс, в котором происходят все настройки и запуск стратегий """

    def __init__(self, client: Services | SandboxService, account_id: str):
        self.client: Services | SandboxService | None = client
        self.account_id: str = account_id
        self.strategies_block: dict[str,list[AssetTemplate]] = {}
        # self.strategies_threads: dict[str, threading.Thread]
        self.worked_assets: list[AssetTemplate] = []  # список объектов, которые были запущены хотя бы раз
        self.logger: Logger = Logger()
        self.assert_constructor: AssetsConstructor = AssetsConstructor(client, account_id)

        self.is_blocked: bool = False # блокировка на изменение настроек
        self.is_sandbox: bool = False # фз зачем вообще
        self.ready_for_work: bool = False

        self.set_last_account_id()

    def run_strategies(self) -> None:
        """ Запуск всех необходимых стратегий """
        if not self.ready_for_work:
            self.logger.error(message="try to start bot without configurate, stop working", module=__name__)
            return
        if self.client is None:
            self.logger.error(message="client was not connect, stop working", module=__name__)
            return

        for strategy_name, strategy_list in self.strategies_block.items():
            self.logger.info(message=f"Starting strategy: [{strategy_name}]",
                             module=__name__)
            try:
                for asset in strategy_list:
                    is_alive_asset = str(asset.is_alive())

                    if asset in self.worked_assets:
                        # возобновление работы 
                        ...
                    else:
                        asset.daemon = True
                        asset.start()
                        self.worked_assets.append(asset)

                    # --добавить сбор потоков для отслеживания статуса работы каждого
                    # данные собираются в self.worked_assets

                    self.logger.info(message=f"{asset.__repr__()} >> START TO WORK", module=__name__)
            except Exception as ex:
                self.logger.error(message=f"error with starting strategy [{strategy_name}]: {ex}", module=__name__)
        self.set_working_status(1)

    def stop_strategies(self):
        """ Остановка работы всех стратегий """
        for strategy, assets in self.strategies_block.items():
            for thread in assets:
                thread.stop()
            self.logger.info(message=f"{strategy} >> STOP STRATEGY", module=__name__)
        self.set_working_status(0)

    def pause_strategies(self):
        """ Временное приостановление работы стратегий """
        for strategy, assets in self.strategies_block.items():
            for asset_thread in assets:
                asset_thread.pause()
            self.logger.info(message=f"{strategy} >> PAUSE STRATEGY", module=__name__)
        self.set_paused_status(1)
    
    def resume_strategies(self):
        """ Возобновление работы стратегий после паузы """
        for strategy, assets in self.strategies_block.items():
            for asset_thread in assets:
                asset_thread.resume()
            self.logger.info(message=f"{strategy} >> RESUME STRATEGY", module=__name__)

        self.set_paused_status(0)

    def set_strategies(self, connect_to_previous: bool, auto_transmission: bool) -> None:
        """
        Конструктор стратегий. Собирает strategies_block
        по конфигурационному листу, либо по последним
        сохраненным данным.
        """

        general_assets_information = {}
        if connect_to_previous:
            self.logger.info(message=f"data will be pulled from the account [{self.account_id}] after the constructor",
                              module=__name__)

        if auto_transmission:
            self.logger.info(message=f"auto transmission is activated",
                             module=__name__)

        if len(self.strategies_block) > 0:
            self.logger.error(message=f"existing data on assets to be destroyed has been found!!!",
                              module=__name__)
            self.strategies_block = {}

        try:
            with open("configs/asset_config.json", "r", encoding="utf-8") as file:
                asset_data: list[dict] = json.load(file)
                self.logger.info(message=f"asset config data has been loaded",
                                 module=__name__)
        except Exception as ex:
            self.logger.error(message=f"error with load asset config data: {ex}",
                                 module=__name__)
            self.ready_for_work = False
            return

        i = 0
        for asset in asset_data:
            try:
                new_asset = self.assert_constructor.construct_asset(**asset)
                if new_asset is None:
                    continue

                if not asset["strategy"] in self.strategies_block.keys():
                    self.strategies_block[asset["strategy"]] = []
                self.strategies_block[asset["strategy"]].append(new_asset)
                general_assets_information[new_asset.figi] = new_asset
                i += 1
                self.logger.info(message=f"asset {new_asset.__repr__()} has been added in strategy {asset["strategy"]}",
                                 module=__name__)

            except Exception as ex:
                self.logger.error(message=f"error with adding asset [{asset["name"]}{asset["figi"]}] in strategy {asset["strategy"]} :: {ex}",
                                  module=__name__)

        if connect_to_previous:
            self.logger.info(
                message=f"start pulling data for synchronization",
                module=__name__)
            tink_data_getter = TinkoffDataGetter(self.client, self.account_id)

            pulled_data = tink_data_getter.get_balance_simple(without_currency=True)
            for figi, amount in pulled_data.items():
                if figi in general_assets_information.keys():
                    edit_asset = general_assets_information[figi]
                    edit_asset.is_bought = True
                    self.logger.info(message=f"PULL DATA: {figi} >> bought {amount}. Set status",
                                     module=__name__)
                    if edit_asset.amount != amount:
                        self.logger.warning(message=f"amount of [{edit_asset.name}{edit_asset.figi}]: {edit_asset.amount}, fact: {amount}. Amount has been edited",
                                            module=__name__)
                        edit_asset.amount = amount
            self.logger.info(
                message=f"data has been synchronized",
                module=__name__)

        if auto_transmission:
            self._auto_transmission_amount(general_assets_information)

        self.ready_for_work = True
        if i == 0:
            self.ready_for_work = False
            self.logger.warning(message=f"there is not a single asset to monitor",
                             module=__name__)

    def _get_current_prices(self, assets_dict: dict[str, AssetTemplate]) -> dict[str, float]:
        """ Получение последней цены для каждого актива по figi """
        res = {}
        for figi in assets_dict.keys():
            try:
                price_data = self.client.market_data.get_last_prices(figi=[figi])
                res[figi] = float(quotation_to_decimal(price_data.last_prices[0].price))
            except Exception as ex:
                self.logger.error(message=f"_GET_CURRENT_PRICE for [{figi}] ERROR :: {ex}", module=__name__)
                pass
        return res

    def _auto_transmission_amount(self, asset_dict: dict[str, AssetTemplate]) -> None:
        """ Автоматическое равное распределение количества каждого актива """

        self.logger.info(
            message=f"AUTO_TRANSMISSION > start auto transmission assets amount",
            module=__name__)
        all_asset_quantity = len(asset_dict)
        accept_money = self.get_money_for_trading

        if not accept_money:
            raise ValueError("incorrect value [money_for_trading] in start_app.ini")

        # поиск ненайденных активов в списке последних цен
        assets_cur_prices = self._get_current_prices(assets_dict=asset_dict)
        not_found = set(asset_dict.keys()).difference(set(assets_cur_prices))
        for not_found_figi in not_found:
            self.logger.warning(message=f"NOT FOUND PRICE for [{not_found_figi}], delete it from asset list",
                                module=__name__)
            asset_dict.pop(not_found_figi)
        self._delete_asset_from_system(figi_list=list(not_found))

        # просмотр уже купленных активов для корректировки цен
        for figi, asset in asset_dict.items():
            if asset.is_bought:
                self.logger.info(message=f"AUTO_TRANSMISSION > asset {asset.__repr__()} has already been purchased: amount {asset.amount}, total {round(asset.amount * assets_cur_prices[figi], 2)}",
                                 module=__name__)
                accept_money -= int(round(asset.amount * assets_cur_prices[figi], 0))
                all_asset_quantity -= 1
        self.logger.info(message=f"AUTO_TRANSMISSION > accept_money = {accept_money}", module=__name__)

        # распределение количества
        money_for_one_part = int(accept_money // all_asset_quantity)
        for figi, cur_price in assets_cur_prices.items():
            accept_amount = int(money_for_one_part // cur_price)
            edit_asset = asset_dict[figi]
            if not edit_asset.is_bought:
                self.logger.info(message=f"AUTO_TRANSMISSION > asset {edit_asset.__repr__()} set amount: {accept_amount}, total_price {round(accept_amount * cur_price, 2)}",
                                 module=__name__)
                edit_asset.amount_auto_transmission = accept_amount
                edit_asset.amount = accept_amount

        self.logger.info(
            message=f"AUTO_TRANSMISSION > end auto transmission",
            module=__name__)


    def _delete_asset_from_system(self, figi_list: list[str]) -> None:
        """ Удаление активов по figi из текущей системы мониторинга """
        for strategy, assets in self.strategies_block.items():
            for asset in assets:
                if asset.figi in figi_list:
                    self.strategies_block[strategy].remove(asset)
                    self.logger.info(message=f"asset {asset.__repr__()} has been deleted",
                                     module=__name__)


    def set_last_account_id(self) -> None:
        """ Установка текущего account_id как последнего рабочего """
        prs = configparser.ConfigParser()
        prs.read("configs/start_app.ini")
        prs["WORK"]["last_account_id"] = self.account_id
        with open("configs/start_app.ini", 'w') as file:
            prs.write(file)
    
    def set_working_status(self, status: Literal[0, 1]) -> None:
        """ Установка статуса работы в файле конфигураций start_app.ini """
        prs = configparser.ConfigParser()
        prs.read("configs/start_app.ini")
        prs["WORK"]["working_status"] = str(status)
        with open("configs/start_app.ini", 'w') as file:
            prs.write(file)
    
    def set_paused_status(self, status: Literal[0, 1]) -> None:
            """ Установка статуса паузы в файле конфигураций start_app.ini """
            prs = configparser.ConfigParser()
            prs.read("configs/start_app.ini")
            prs["WORK"]["paused"] = str(status)
            with open("configs/start_app.ini", 'w') as file:
                prs.write(file)

    @property
    def get_money_for_trading(self) -> int | None:
        """ Получить разрешенное количество денег для проведения операций """
        prs = configparser.ConfigParser()
        prs.read("configs/start_app.ini")
        try:
            res = int(prs["START_PARAMETERS"]["money_for_trading"])
            return res
        except Exception as ex:
            self.logger.error(message=f"GET_MONEY_TRADING ERROR :: {ex}", module=__name__)
            return None


    @property
    def get_work_status(self) -> Literal['0', '1']:
        """ Получить статус работы сервиса """
        prs = configparser.ConfigParser()
        prs.read("configs/start_app.ini")
        return prs["WORK"]["working_status"]

    @property
    def get_paused_status(self) -> Literal['0', '1']:
        """ Получить статус паузы сервиса """
        prs = configparser.ConfigParser()
        prs.read("configs/start_app.ini")
        return prs["WORK"]["paused"]
    