from datetime import datetime
from typing import Generator

from tinkoff.invest import CandleInterval, HistoricCandle
from tinkoff.invest.services import Services
from tinkoff.invest.utils import now, money_to_decimal, quotation_to_decimal


class TinkoffDataGetter:
    """ Класс для запросов информации """

    def __init__(self, client: Services, account_id: str) -> None:
        self.client = client
        self.account_id: str = account_id

    def get_candles(
            self,
            figi: str,
            interval: CandleInterval,
            from_: datetime,
            to: datetime = now()
    ) ->  Generator[HistoricCandle, None, None]:
        """
        Получение свечей за определенный период по определенному активу
        :param figi: figi индикатор актива
        :param interval: интервал свечей
        :param from_: с какого периода свечи
        :param to: до какого периода свечи
        """

        return self.client.get_all_candles(
            figi=figi,
            interval=interval,
            from_=from_,
            to=to
        )
    

    def get_balance(self) -> dict:
        """ 
        Получение данных баланса счета, каждого актива отдельно 
        
        Вид возвращаеммых данных:
        {
            "currency": 
            [
                {
                    "figi": ...,
                    "instr_type": currency_type,
                    "amount": ...,
                    "cur_price_for_one": ...,
                    "cur_price": ...,
                    "ticker": ...,
                }
            ],
            "etf":
            [
                {...},
                {...},
            ],
            ...
        }
        """
        
        report_data = {}
        data = self.client.operations.get_portfolio(account_id=self.account_id)
        for pos in data.positions:
            figi = pos.figi
            instr_type = pos.instrument_type
            amount = round(float(quotation_to_decimal(pos.quantity)), 2)
            cur_price_for_one = float(money_to_decimal(pos.current_price))
            cur_price = round(cur_price_for_one * amount, 2)
            ticker = pos.ticker
            if not instr_type in report_data.keys():
                report_data[instr_type] = [] 
            report_data[instr_type].append({
                "figi": figi,
                "instr_type": instr_type,
                "amount": amount,
                "cur_price_for_one": cur_price_for_one,
                "cur_price": cur_price,
                "ticker": ticker,
            })
        
        return report_data
            