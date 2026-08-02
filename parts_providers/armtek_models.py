from datetime import datetime
from typing import Annotated, Any

import pydantic
from pydantic import ConfigDict, BeforeValidator, PlainSerializer


class ArmTekResponse(pydantic.BaseModel):
    """
    Базовое тело ответа от ArmTEK
    """
    STATUS: int
    MESSAGES: list[str]


class WarehouseData(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    SKLNAME: str


class UserVKorg_FIELD(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    VKORG: str
    PROGRAM_NAME: str


class UserVKorgResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: list[UserVKorg_FIELD]


#
# Описание структуры клиента
#
class ZA_TAB_Item(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    KUNNR: str
    DEFAULT: int
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str


class CONTACT_TAB_Item(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    PARNR: str
    DEFAULT: int
    FNAME: str
    LNAME: str
    MNAME: str
    PHONE: str
    EMAIL: str


class RG_TAB_Item(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    KUNNR: str
    DEFAULT: int
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str
    ZA_TAB: list[ZA_TAB_Item]
    CONTACT_TAB: list[CONTACT_TAB_Item]


class User_STRUCTURE_FIELD(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    KUNAG: str
    VKORG: str
    SNAME: str
    FNAME: str
    ADRESS: str
    PHONE: str
    RG_TAB: list[RG_TAB_Item]


class UserInfoResp(pydantic.BaseModel):
    STRUCTURE: User_STRUCTURE_FIELD


class UserInfoResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: UserInfoResp


#
# Описание результата поиска по артиклю
#
class SearchPin_ITEM(pydantic.BaseModel):
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

    RESP: list[SearchPin_ITEM] | SearchPinMsg


#
# Описание результата поиска по ассортименту
#
class AssortmentSearch_ITEM(pydantic.BaseModel):
    model_config = ConfigDict(extra='ignore')

    PIN: str | None = None
    BRAND: str | None = None
    NAME: str | None = None


class AssortmentSearchResponse(ArmTekResponse):
    model_config = ConfigDict(extra='ignore')

    RESP: list[AssortmentSearch_ITEM] | SearchPinMsg


DLVDT_FORMAT = "%Y%m%d%H%M%S"


def _parse_dlvdt(value: Any) -> Any:
    """Accept 'YYYYMMDDHHMMSS' strings; treat empty/blank as None."""
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        return datetime.strptime(value, DLVDT_FORMAT)
    return value


def _dump_dlvdt(value: datetime | None) -> str | None:
    return value.strftime(DLVDT_FORMAT) if value is not None else None


SAPTimestamp = Annotated[
    datetime | None,
    BeforeValidator(_parse_dlvdt),
    PlainSerializer(_dump_dlvdt, return_type=str, when_used="unless-none"),
]


#
# Описание результатов создания заказа
#
class OrderItemResult_ITEM(pydantic.BaseModel):
    POSID: str | None = None
    POSNR: str | None = None
    KEYZAK: str | None = None
    NUM_ZAK: str | None = None
    KWMENG: int | None = None
    RVALUE: int | None = None
    PRICE: str | None = None
    WAERS: str | None = None
    DLVDT: SAPTimestamp = None
    VBELN: str | None = None
    BLOCK: str | None = None
    ERROR: str | None = None


class CreateOrderResponse_ITEM(pydantic.BaseModel):
    PIN: str | None = None
    BRAND: str | None = None
    KEYZAK: str | None = None
    KWMENG: int | None = None
    PRICEMAX: str | None = None
    DATEMAX: str | None = None
    COMMENT: str | None = None
    COMPL_DLV: str | None = None
    ARTID: str | None = None
    RESULT: list[OrderItemResult_ITEM] | None = None
    REMAIN: int | None = None
    ERROR: int | None = None
    ERROR_MESSAGE: str | None = None