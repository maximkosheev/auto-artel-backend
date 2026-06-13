from datetime import datetime


def parse_date(date, parse_format):
    if date is None:
        return None
    return datetime.strptime(date, parse_format)
