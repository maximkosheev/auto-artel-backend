from rest_framework import serializers

from utils import phone_utils


def phone_validator(value):
    if not phone_utils.validate(value):
        raise serializers.ValidationError("Phone does not match russian phone pattern")
