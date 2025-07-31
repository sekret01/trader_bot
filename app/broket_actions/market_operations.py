from tinkoff.invest.services import Services
from tinkoff.invest import OrderType, OrderDirection
from tinkoff.invest.schemas import PostOrderResponse


class TinkoffMarketOperations:
    """ Класс для проведения основных торговых операций """

    def __init__(self, client: Services):
        self.client = client
        self.account_id = self.client.users.get_accounts().accounts[0].id

    def buy_asset(self, figi: str, amount: int) -> PostOrderResponse:
        """
        Покупка актива
        :param figi: figi-идентификатор актива
        :param amount: количество лотов на покупку
        """
        post_order_response = self.client.orders.post_order(
            figi=figi,
            quantity=amount,
            account_id=self.account_id,
            order_type=OrderType.ORDER_TYPE_MARKET,
            direction=OrderDirection.ORDER_DIRECTION_BUY
        )
        return post_order_response

    def sell_asset(self, figi: str, amount: int) -> PostOrderResponse:
        """
        Продажа актива
        :param figi: figi-идентификатор актива
        :param amount: количество лотов на продажу
        """
        post_order_response = self.client.orders.post_order(
            figi=figi,
            quantity=amount,
            account_id=self.account_id,
            order_type=OrderType.ORDER_TYPE_MARKET,
            direction=OrderDirection.ORDER_DIRECTION_SELL
        )
        return post_order_response