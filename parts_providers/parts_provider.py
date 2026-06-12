from abc import ABC, abstractmethod


class AutoPartsProvider(ABC):

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def assortment_search(self, pin):
        """
        Выполняет поиск производителей запчасти по её артиклю
        @param pin: артикул
        """
        pass

    @abstractmethod
    def search(self, pin, manufacture):
        """
        Выполняет поиск запчасти по её артиклю
        @param pin: артикул
        @param manufacture: производитель
        @return список SearchResultItem
        """
    pass


class SearchResultItem:
    def __init__(self):
        self.article_number = None
        self.manufacture = None
        self.name = None
        self.price = None
        self.count = None
        self.delivery_time = None
        self.warehouse_location = None


class AssortmentSearchResultItem:
    def __init__(self):
        self.article_number = None
        self.manufacture = None
        self.name = None
