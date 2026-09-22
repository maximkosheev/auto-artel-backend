import logging
import os
from datetime import datetime
from json import JSONDecodeError

import pydantic
import requests
from django.core.cache import cache

from . import ProviderApiError
from .armtek_models import WarehouseData, SearchPinResponse, AssortmentSearchResponse, UserInfoResponse, \
    UserVKorgResponse, CreateOrderResponse
from .parts_provider import AutoPartsProvider, AssortmentSearchResultItem, SearchResultItem, CreateOrderResult

logger = logging.getLogger(__name__)

USER_VKORG_LIST_URL = 'http://ws.armtek.ru/api/ws_user/getUserVkorgList?format=json'
USER_INFO_URL = 'http://ws.armtek.ru/api/ws_user/getUserInfo?format=json'
SEARCH_URL = 'http://ws.armtek.ru/api/ws_search/search?format=json'
ASSORTMENT_SEARCH_URL = 'http://ws.armtek.ru/api/ws_search/assortment_search?format=json'
STORE_URL = 'http://ws.armtek.ru/api/ws_user/getStoreList?format=json'
CREATE_ORDER_URL = 'http://ws.armtek.ru/api/ws_order/createOrder?format=json'


class ArmTekProvider(AutoPartsProvider):

    def __init__(self):
        self.login = os.getenv("ARMTEK_LOGIN")
        self.password = os.getenv("ARMTEK_PASSWORD")
        self.session = requests.Session()
        self.session.auth = (self.login, self.password)
        self._vkorg = None
        self._userInfo = None

    def init(self):
        pass

    @property
    def vkorg(self):
        if self._vkorg:
            return self._vkorg

        logger.debug("ArmTek getting vkorg")
        response = self.session.get(USER_VKORG_LIST_URL)
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.debug(f"ArmTek get VKORG response: {response_data}")
                api_response = UserVKorgResponse.model_validate(response_data)
                self._vkorg = api_response.RESP[0].VKORG
                return self._vkorg
            except pydantic.ValidationError as e:
                logger.error(f"Unexpected response format: {e}", exc_info=True)
                raise ProviderApiError('Ошибка обработки ответа от поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

    @property
    def user_info(self):
        if self._userInfo:
            return self._userInfo

        logger.debug("ArmTek getting user info")
        response = self.session.post(USER_INFO_URL, data={
            'VKORG': self.vkorg
        })
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.debug(f"ArmTek get UserInfo response: {response_data}")
                api_response = UserInfoResponse.model_validate(response_data)
                self._userInfo = api_response.RESP.STRUCTURE
                return self._userInfo
            except pydantic.ValidationError as e:
                logger.error(f"Unexpected response format: {e}", exc_info=True)
                raise ProviderApiError('Ошибка обработки ответа от поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

    @property
    def buyer(self):
        return self.user_info.RG_TAB[0].KUNNR

    def assortment_search(self, pin):
        logger.debug(f"ArmTek assortment_search for pin: {pin}")
        response = self.session.post(ASSORTMENT_SEARCH_URL, data={
            'VKORG': self.vkorg,
            'PIN': pin,
        })
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.debug(f"ArmTek assortment_search response: {response_data}")
                api_response = AssortmentSearchResponse.model_validate(response_data)
                if isinstance(api_response.RESP, list):
                    return [self.__map_assortment_item_to_result(item) for item in api_response.RESP]
                return []
            except JSONDecodeError as ex:
                logger.error(f"Parse error occurred: {ex}, when parsing data: {response.text}", exc_info=True)
                raise ProviderApiError('Ошибка обработки ответа от поставщика')
            except pydantic.ValidationError as e:
                logger.error(f"Unexpected response format: {e}", exc_info=True)
                raise ProviderApiError('Ошибка обработки ответа от поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.text}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

    def __map_assortment_item_to_result(self, item):
        result = AssortmentSearchResultItem()
        result.article_number = item.PIN
        result.manufacture = item.BRAND
        result.name = item.NAME
        return result

    def search(self, pin, manufacture):
        logger.debug(f"ArmTek search for pin: {pin}, manufacture: {manufacture}")
        response = self.session.post(SEARCH_URL, data={
            'VKORG': self.vkorg,
            'KUNNR_RG': self.buyer,
            'PIN': pin,
            'BRAND': manufacture,
            'QUERY_TYPE': '2'
        })
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.debug(f"ArmTek search response: {response_data}")
                api_response = SearchPinResponse.model_validate(response_data)
                if type(api_response.RESP) is list:
                    return list(map(lambda RESP_Item:
                                    self.__map_search_pin_item_to_search_result_item(RESP_Item),
                                    api_response.RESP))
                else:
                    return []
            except JSONDecodeError as ex:
                logger.error(f"Parse error occurred: {ex}, when parsing data: {response.text}", exc_info=True)
                raise ProviderApiError('Ошибка запроса данных у поставщика')
            except Exception as e:
                logger.error(f"Случилась ошибка: {e}", exc_info=True)
                raise ProviderApiError('Ошибка запроса данных у поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

    def __map_search_pin_item_to_search_result_item(self, search_pin_item):
        def safe_float(value):
            try:
                return float(value)
            except ValueError:
                return None

        result = SearchResultItem()
        result.internal_art_id = search_pin_item.ARTID
        result.article_number = search_pin_item.PIN
        result.manufacture = search_pin_item.BRAND
        result.name = search_pin_item.NAME
        result.purchase_price = safe_float(search_pin_item.PRICE)
        result.total_count = search_pin_item.RVALUE
        result.multiplicity = search_pin_item.RDPRF
        if search_pin_item.DLVDT:
            result.delivery_time = datetime.strptime(search_pin_item.DLVDT, '%Y%m%d%H%M%S')
        result.warehouse_location = self.__map_warehouse_code(search_pin_item.KEYZAK)
        result.warehouse_code = search_pin_item.KEYZAK
        return result

    def __map_warehouse_code(self, warehouse_code):
        warehouse_data = WarehouseData.model_validate(cache.get(warehouse_code, {'SKLNAME': 'Неизвестный склад'}))
        return warehouse_data.SKLNAME

    def create_order(self, order_items: list):
        def flatten(data, prefix=""):
            """dict/list -> [('ITEMS[0][PIN]', 'MD755526'), ...]"""
            out = []
            if isinstance(data, dict):
                items = data.items()
            elif isinstance(data, (list, tuple)):
                items = enumerate(data)
            else:
                return [(prefix, str(data))]
            for key, value in items:
                name = f"{prefix}[{key}]" if prefix else str(key)
                out.extend(flatten(value, name))
            return out

        def is_item_supported(item):
            if item.provider is None:
                return False
            elif item.provider.upper() == 'ARMTEK':
                return True
            else:
                return False

        items = list(filter(lambda item: is_item_supported(item), order_items))

        logger.debug(f"Create order with items: {items}")

        payload = {
            'VKORG': self.vkorg,
            'KUNRG': self.buyer,
            'ITEMS': list(map(lambda o: {
                'PIN': o.article_number,
                'BRAND': o.manufacture,
                'KWMENG': o.count,
                'KEYZAK': o.warehouse_code,
                'PRICEMAX': o.purchase_price,
                'COMPL_DLV': "1"
            }, items))
        }

        form_data = [(name, value) for name, value in flatten(payload)]
        logger.debug(f"Create order request payload: {form_data}")

        response = self.session.post(CREATE_ORDER_URL, data=form_data)

        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.debug(f"ArmTek create order response: {response_data}")
                api_response = CreateOrderResponse.model_validate(response_data)
                if api_response.RESP is not None:
                    response_items = api_response.RESP.ITEMS
                    result = CreateOrderResult()
                    result.response_payload = response_data
                    with_error = 0
                    for resp_item in response_items:
                        result_item = {
                            'article_number': resp_item.PIN,
                            'manufacture': resp_item.BRAND,
                            'warehouse_code': resp_item.KEYZAK,
                            'error': resp_item.ERROR != 0 if resp_item.ERROR is not None else False,
                            'error_message': resp_item.ERROR_MESSAGE,
                            'remain': resp_item.REMAIN if resp_item.REMAIN is not None else 0
                        }
                        logger.info(f"Adding result_item: {result_item}")
                        result.items.append(result_item)
                        if result_item['error']:
                            with_error += 1
                    if with_error:
                        if with_error == len(response_items):
                            result.success = CreateOrderResult.FAILED
                        else:
                            result.success = CreateOrderResult.HALF
                    else:
                        result.success = CreateOrderResult.SUCCESS
                    return result
                else:
                    logger.error(f"ArmTek response messages: {api_response.MESSAGES}")
                    raise ProviderApiError('При создании заказа поставщик вернул ошибку')
            except JSONDecodeError as ex:
                logger.error(f"Parse error occurred: {ex}, when parsing data: {response.text}", exc_info=True)
                raise ProviderApiError('Ошибка обработки ответа от поставщика')
            except ProviderApiError as e:
                raise e
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
                raise ProviderApiError('Ошибка запроса данных у поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')
