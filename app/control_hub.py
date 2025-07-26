from typing import Literal, Optional
import threading
import json

from tinkoff.invest import Client, AioRequestError, InstrumentType, CandleInterval
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.services import Services, SandboxService

from . import Strategy
from .asset_templates import TrendFollowing
from .asset_templates import AssetTemplate, CandleTemplate
from .logger import Logger
from .assets_constructor import AssetsConstructor


# вынести в отдельный модуль вместе с конструктором активов
TEMPS: dict[str,type[AssetTemplate]] = {
    "candle": CandleTemplate
}
# вынести в отдельный модуль вместе с конструктором активов
STRATS = {
    "trendfollowing": TrendFollowing
}


class ControlHub:
    """ Класс, в котором происходят все настройки и запуск стратегий """

    def __init__(self, client: Services | SandboxService):
        self.client: Services | SandboxService | None = client
        self.strategies_block: dict[str,list[AssetTemplate]] = {}
        self.logger: Logger = Logger()
        self.assert_constructor: AssetsConstructor = AssetsConstructor(client)

        self.is_blocked: bool = False # блокировка на изменение настроек
        self.is_sandbox: bool = False # фз зачем вообще
        self.ready_for_work: bool = False

    def run_strategies(self) -> None:
        """ Запуск всех необходимых стратегий """
        if not self.ready_for_work:
            self.logger.warning(message="try to start bot without configurate, stop working", module=__name__)
            return
        if self.client is None:
            self.logger.warning(message="client was not connect, stop working", module=__name__)
            return

        for strategy_name, strategy_list in self.strategies_block.items():
            self.logger.info(message=f"Starting strategy: [{strategy_name}]",
                             module=__name__)
            try:
                for asset in strategy_list:
                    asset.daemon = True  # для завершения работы со всеми потоками
                    asset.start()
                    # добавить сбор потоков для отслеживания статуса работы каждого

                    self.logger.info(message=f"{asset.__repr__()} >> START TO WORK", module=__name__)
            except Exception as ex:
                self.logger.error(message=f"error with starting strategy: {ex}", module=__name__)

    def stop_strategies(self):
        """ Остановка работы всех стратегий """
        for strategy, assets in self.strategies_block.items():
            for thread in assets:
                thread.stop()
            self.logger.info(message=f"{strategy} >> STOP STRATEGY", module=__name__)


    # def set_client(
    #         self,
    #         token: str,
    #         client_type: Literal["standard", "sandbox"],
    #         token_name: Optional[str] = "Unknown"
    # ) -> None:
    #     """
    #     Подключение клиента по-заданному токену.
    #     Данные подставлять из файла конфигураций.
    #     :param token: Токен для подключения к счету
    #     :param client_type: Тип клиента (обычный, песочница)
    #     :param token_name: Название токена для идентификации (необязательно)
    #     :return: None
    #     """
    #     current_client = Client if client_type == "standard" else SandboxClient
    #     try:
    #         with current_client(token=token) as client:
    #             self.client = client
    #             self.ready_for_work = True
    #             self.logger.info(message=f"connect for client, type:{client_type}, token_name:{token_name}",
    #                              module=__name__)
    #
    #     except AioRequestError as ex:
    #         self.ready_for_work = False
    #         self.logger.error(message=f"cant connect to client, type:{client_type}, token_name:{token_name}, ex::{ex} ",
    #                           module=__name__)

    def set_strategies(self) -> None:
        """
        Конструктор стратегий. Собирает strategies_block
        по конфигурационному листу, либо по последним
        сохраненным данным.
        """
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

        # вынести в отдельный модуль вместе с конструктором активов
        i = 0
        for asset in asset_data:
            try:
                new_asset = self.assert_constructor.construct_asset(**asset)
                if new_asset is None:
                    continue

                if not asset["strategy"] in self.strategies_block.keys():
                    self.strategies_block[asset["strategy"]] = []
                self.strategies_block[asset["strategy"]].append(new_asset)
                i += 1
                self.logger.info(message=f"asset {new_asset.__repr__()} has been added in strategy {asset["strategy"]}",
                                 module=__name__)

            except Exception as ex:
                self.logger.error(message=f"error with adding asset [{asset["name"]}{asset["figi"]}] in strategy {asset["strategy"]} :: {ex}",
                                  module=__name__)

            self.ready_for_work = True
            if i == 0:
                self.ready_for_work = False
                self.logger.warning(message=f"there is not a single asset to monitor",
                                 module=__name__)
