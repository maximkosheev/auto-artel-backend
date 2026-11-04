import json
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

    @abstractmethod
    def create_order(self, order_items: list):
        """
        Создание заказа
        @param order_items: позиции заказа
        @return: json ответ API поставщика
        """
        return json.loads("{}")


class SearchResultItem:
    def __init__(self):
        self.internal_art_id = None
        self.article_number = None
        self.manufacture = None
        self.name = None
        self.purchase_price = None
        self.total_count = None
        self.delivery_time = None
        self.warehouse_location = None
        self.warehouse_code = None
        self.multiplicity = 1


class AssortmentSearchResultItem:
    def __init__(self):
        self.article_number = None
        self.manufacture = None
        self.name = None


class CreateOrderResult:
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    HALF = 'HALF'

    def __init__(self):
        self.success = False
        self.response_payload = {}
        self.items = []
