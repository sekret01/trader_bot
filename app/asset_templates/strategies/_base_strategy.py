import abc

class Strategy(abc.ABC):
    """ Абстрактный класс для оформления стратегий """
    @abc.abstractmethod
    def __init__(self, *args, **kwargs): pass

    @abc.abstractmethod
    def __repr__(self): pass

    @abc.abstractmethod
    def prepare_data(self, *args, **kwargs): pass

    @abc.abstractmethod
    def get_signal(self): pass

    @abc.abstractmethod
    def to_json(self): pass

    @staticmethod
    @abc.abstractmethod
    def from_json(data: dict): pass
