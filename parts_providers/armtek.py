import logging
import os
from json import JSONDecodeError

import pydantic
import requests
from django.core.cache import cache
from pydantic import ConfigDict
from datetime import datetime

from . import ProviderApiError
from .parts_provider import AutoPartsProvider, AssortmentSearchResultItem, SearchResultItem

logger = logging.getLogger(__name__)

USER_VKORG_LIST_URL = 'http://ws.armtek.ru/api/ws_user/getUserVkorgList?format=json'
USER_INFO_URL = 'http://ws.armtek.ru/api/ws_user/getUserInfo?format=json'
SEARCH_URL = 'http://ws.armtek.ru/api/ws_search/search?format=json'
ASSORTMENT_SEARCH_URL = 'http://ws.armtek.ru/api/ws_search/assortment_search?format=json'
STORE_URL = 'http://ws.armtek.ru/api/ws_user/getStoreList?format=json'


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
        result = SearchResultItem()
        result.internal_art_id = search_pin_item.ARTID
        result.article_number = search_pin_item.PIN
        result.manufacture = search_pin_item.BRAND
        result.name = search_pin_item.NAME
        result.price = search_pin_item.PRICE
        result.count = search_pin_item.RVALUE
        if search_pin_item.DLVDT:
            result.delivery_time = datetime.strptime(search_pin_item.DLVDT, '%Y%m%d%H%M%S')
        result.warehouse_location = self.__map_warehouse_code(search_pin_item.KEYZAK)
        return result

    def __map_warehouse_code(self, warehouse_code):
        warehouse_data = WarehouseData.model_validate(cache.get(warehouse_code, {'SKLNAME': 'Неизвестный склад'}))
        return warehouse_data.SKLNAME


class UserVKorg(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    VKORG: str
    PROGRAM_NAME: str


class ZA_TABItem(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    KUNNR: str
    DEFAULT: int
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str


class CONTACT_TABItem(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    PARNR: str
    DEFAULT: int
    FNAME: str
    LNAME: str
    MNAME: str
    PHONE: str
    EMAIL: str


class RG_TABItem(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    KUNNR: str
    DEFAULT: int
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str
    ZA_TAB: list[ZA_TABItem]
    CONTACT_TAB: list[CONTACT_TABItem]


class User_STRUCTURE(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    KUNAG: str
    VKORG: str
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str
    RG_TAB: list[RG_TABItem]


class ArmTekResponse(pydantic.BaseModel):
    STATUS: int
    MESSAGES: list[str]


class UserVKorgResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: list[UserVKorg]


class UserInfoResp(pydantic.BaseModel):
    STRUCTURE: User_STRUCTURE


class UserInfoResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: UserInfoResp


class SearchPinItem(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore', )

    PIN: str | None = None
    BRAND: str | None = None
    NAME: str | None = None
    ARTID: str | None = None
    PARNR: str | None = None
    KEYZAK: str | None = None
    RVALUE: str | None = None
    RETDAYS: str | None = None
    RDPRF: str | None = None
    MINBM: str | None = None
    VENSL: str | None = None
    PRICE: str | None = None
    WAERS: str | None = None
    DLVDT: str | None = None
    WRNTDT: str | None = None
    ANALOG: str | None = None
    TYPEB: str | None = None
    DSPEC: str | None = None
    RCOST: str | None = None
    MRKBY: str | None = None
    PNOTE: str | None = None
    IMP_ADD: str | None = None
    SELLP: str | None = None
    REST_ADD: str | None = None
    REST_ADD_P: str | None = None


class SearchPinMsg(pydantic.BaseModel):
    MSG: str | None = None


class SearchPinResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: list[SearchPinItem] | SearchPinMsg


class WarehouseData(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    SKLNAME: str


class AssortmentSearchItem(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    PIN: str | None = None
    BRAND: str | None = None
    NAME: str | None = None


class AssortmentSearchResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: list[AssortmentSearchItem] | SearchPinMsg

