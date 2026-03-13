import logging
import os
from json import JSONDecodeError

import pydantic

import requests
from pydantic import ConfigDict

from . import ProviderApiError
from .parts_provider import AutoPartsProvider, SearchResultItem

logger = logging.getLogger(__name__)

USER_VKORG_LIST_URL = 'http://ws.armtek.ru/api/ws_user/getUserVkorgList?format=json'
USER_INFO_URL = 'http://ws.armtek.ru/api/ws_user/getUserInfo?format=json'
SEARCH_URL = 'http://ws.armtek.ru/api/ws_search/search?format=json'


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
                logger.error(f"Unexpected response format: {e}")
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
                logger.error(f"Unexpected response format: {e}")
                raise ProviderApiError('Ошибка обработки ответа от поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

    @property
    def buyer(self):
        return self.user_info.RG_TAB[0].KUNNR

    def search(self, pin):
        logger.debug(f"ArmTek search for pin: {pin}")
        response = self.session.post(SEARCH_URL, data={
            'VKORG': self.vkorg,
            'KUNNR_RG': self.buyer,
            'PIN': pin
        })
        if response.status_code == 200:
            try:
                response_data = response.json()
                api_response = SearchPinResponse.model_validate(response_data)
                if type(api_response.RESP) is list:
                    return list(map(lambda RESP_Item:
                                    self.__map_search_pin_item_to_search_result_item(RESP_Item),
                                    api_response.RESP))
                else:
                    return []
            except JSONDecodeError as ex:
                logger.error(f"Parse error occurred: {ex}, when parsing data: {response.json()}")
                raise ProviderApiError('Ошибка запроса данных у поставщика')
            except Exception as e:
                logger.error(f"Случилась ошибка: {e}")
                raise ProviderApiError('Ошибка запроса данных у поставщика')
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

    def __map_search_pin_item_to_search_result_item(self, search_pin_item):
        result = SearchResultItem()
        result.article_number = search_pin_item.ARTID
        result.manufacture = search_pin_item.BRAND
        result.name = search_pin_item.NAME
        result.price = search_pin_item.PRICE
        result.count = search_pin_item.RVALUE
        result.delivery_time = search_pin_item.DLVDT
        result.warehouse_location = search_pin_item.KEYZAK
        return result


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
