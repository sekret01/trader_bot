import abc

class Strategy(abc.ABC):
    """ Абстрактный класс для оформления стратегий """

    @abc.abstractmethod
    def get_signal(self): pass

