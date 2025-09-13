import re


def validate(value: str) -> bool:
    pattern = re.compile("^\\+7\\d{10}$", re.RegexFlag.M)
    return re.match(pattern, value) is not None


def before_save_to_db(value: str) -> str:
    return re.sub("[^0-9]", "", value)


def after_read_from_db(value: str) -> str:
    if value and not value.startswith("+"):
        return f"+{value}"
    return value
