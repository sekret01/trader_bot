from tinkoff.invest import CandleInterval, InstrumentType
from tinkoff.invest.services import Services

# templates
from .asset_templates import (
AssetTemplate,
CandleTemplate
)

# strategies
from .asset_templates import (
Strategy,
TrendFollowing
)

from .logger import Logger

"""

ДОБАВЛЯТЬ ФУНКЦИИ В СЛЕДУЮЩИЕ МЕСТА:
 - __init__ / self.templates  >> добавлять новые шаблоны
 - __init__ / self.strategies  >> добавлять новые стратегии
 - __init__ / self.router_by_functions  >> добавлять новые функции для 
                                            создания объектов актива 
                                            (при появлении новых шаблонов)

"""


class AssetsConstructor:
    """ Класс для создания объектов стратегий по конфигурациям """

    def __init__(self, client: Services, account_id: str) -> None:
        self.logger = Logger()
        self.client: Services = client
        self.account_id = account_id

        # расширять по мере добавления новых шаблонов
        self.templates: dict[str, type[AssetTemplate]] = {
            "candle": CandleTemplate
        }

        # расширять по мере добавления новых стратегий
        self.strategies: dict[str, type[Strategy]] = {
            "trendfollowing": TrendFollowing
        }

        # расширять по мере добавления новых стратегий
        self.router_by_functions: dict[type[AssetTemplate], callable] = {
            CandleTemplate: self.build_candle_template
        }

    def construct_asset(self, **kwargs) -> AssetTemplate | None:
        """ Конструктор стратегии для актива """
        mandatory_keys = [
            'name',
            'figi',
            'amount',
            'days_back',
            'timeframe',
            'check_interval',
            'type',
            'strategy',
            'template',
            'construct_data'
        ]
        name = kwargs.get("name") or "unknown_name"
        figi = kwargs.get("figi") or "unknown_figi"

        for key in mandatory_keys:
            if not key in kwargs.keys():

                self.logger.warning(message=f"{name}:{figi} have not a mandatory key: [{key}]. Stop constructing",
                                    module=__name__)
                return None

        strategy_type: type[Strategy] = self.determine_strategy(strategy_name=kwargs["strategy"])
        if strategy_type is None:
            self.logger.warning(message=f"{name}:{figi} strategy [{kwargs["strategy"]}] is unknown. Stop constructing",
                                module=__name__)
            return None
        strategy: Strategy = strategy_type(**kwargs["construct_data"], asset_info=f"{name}:[figi={figi}]")

        template_type: type[AssetTemplate] = self.determine_template(kwargs["template"])
        if template_type is None:
            self.logger.warning(message=f"{name}:{figi} template [{kwargs["template"]}] is unknown. Stop constructing",
                                module=__name__)
            return None

        template = self.build_asset(
            temp_type=template_type,
            row_data=kwargs,
            strategy=strategy
        )
        if template is None:
            self.logger.warning(message=f"{name}:{figi} template [{kwargs["template"]}] did not find in routs. Stop constructing",
                                module=__name__)
            return None

        self.logger.info(message=f"build asset :: {template.full_info()}", module=__name__)
        return template


    def build_asset(self, temp_type: type[AssetTemplate], row_data: dict, strategy: Strategy) -> AssetTemplate | None:
        """ Создание объекта актива """
        func = self.router_by_functions.get(temp_type)
        if func is None: return None
        return func(row_data, strategy)

    # ==============================================

    def determine_template(self, template_name: str) -> type[AssetTemplate] | None:
        """ Определение шаблона актива, который необходимо создать """
        return self.templates.get(template_name)

    def determine_strategy(self, strategy_name: str) -> type[Strategy] | None:
        """ Определение стратегии, необходимой подключить в шаблон актива """
        return self.strategies.get(strategy_name)

    # ===============================================

    def build_candle_template(self, row_data: dict, strategy: Strategy) -> AssetTemplate:
        """ Создание объекта актива по шаблону CandleTemplate """
        return CandleTemplate(
            client=self.client,
            account_id=self.account_id,
            figi=row_data["figi"],
            name=row_data["name"],
            amount=row_data["amount"],
            days_back=row_data["days_back"],
            timeframe=CandleInterval(row_data["timeframe"]),
            check_interval=row_data["check_interval"],
            type_=InstrumentType(row_data["type"]),
            strategy=strategy
        )