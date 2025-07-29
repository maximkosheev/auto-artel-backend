import re
from rest_framework import serializers


def phone_validator(value):
    pattern = re.compile("^(8|\\+7)(\\s|\\(|-)?(\\d{3})(\\s|\\)|-)?(\\d{3})(\\s|-)?(\\d{2})(\\s|-)?(\\d{2})$",
                         re.RegexFlag.M)
    if not re.match(pattern, value):
        raise serializers.ValidationError("Phone does not match russian phone pattern")
