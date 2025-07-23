import abc

class Strategy(abc.ABC):
    """ Абстрактный класс для оформления стратегий """

    @abc.abstractmethod
    def prepare_data(self, *args, **kwargs): pass

    @abc.abstractmethod
    def get_signal(self): pass

