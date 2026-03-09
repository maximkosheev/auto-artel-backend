import logging
import os
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
    def userInfo(self):
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
        return self.userInfo.RG_TAB[0].KUNNR

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
                logger.debug(f"ArmTek search pin '{pin}' response: {response_data}")
            except Exception as e:
                logger.error("")
        else:
            logger.error(f"ArmTek response status: {response.status_code}, body: {response.json()}")
            raise ProviderApiError('Ошибка запроса данных у поставщика')

        item1 = SearchResultItem()
        item1.article_number = pin
        item1.manufacture = "FORD"
        item1.name = "Какая-то хуйня"
        item1.price = 1000.00
        item1.count = 100
        item1.delivery_time = "10 дней"
        item1.warehouse_location = "Челябинск"

        return [
            item1
        ]


class UserVKorg(pydantic.BaseModel):
    model_config = ConfigDict(extra='allow')

    VKORG: str
    PROGRAM_NAME: str


class ZA_TAB_Item(pydantic.BaseModel):
    model_config = ConfigDict(extra='allow')

    KUNNR: str
    DEFAULT: int
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str


class CONTACT_TAB_Item(pydantic.BaseModel):
    model_config = ConfigDict(extra='allow')

    PARNR: str
    DEFAULT: int
    FNAME: str
    LNAME: str
    MNAME: str
    PHONE: str
    EMAIL: str


class RG_TAB_Item(pydantic.BaseModel):
    model_config = ConfigDict(extra='allow')

    KUNNR: str
    DEFAULT: int
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str
    ZA_TAB: list[ZA_TAB_Item]
    CONTACT_TAB: list[CONTACT_TAB_Item]


class User_STRUCTURE(pydantic.BaseModel):
    model_config = ConfigDict(extra='allow')

    KUNAG: str
    VKORG: str
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str
    RG_TAB: list[RG_TAB_Item]

class ArmTekResponse(pydantic.BaseModel):
    STATUS: int
    MESSAGES: list[str]


class UserVKorgResponse(ArmTekResponse):
    model_config = ConfigDict(extra='allow')

    RESP: list[UserVKorg]


class UserInfoResp(pydantic.BaseModel):
    STRUCTURE: User_STRUCTURE


class UserInfoResponse(ArmTekResponse):
    model_config = ConfigDict(extra='allow')

    RESP: UserInfoResp


