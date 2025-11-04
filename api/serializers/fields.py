from rest_framework import serializers

from api import validators
from utils import phone_utils


class ClientPhoneField(serializers.CharField):
    default_validators = [validators.phone_validator]

    def to_internal_value(self, data):
        return phone_utils.before_save_to_db(data)

    def run_validators(self, value):
        # Добавляем лидирующий символ '+' перед значением, чтобы пройти валидацию.
        # Это нужно, потому что в БД телефон храниться без '+', но для валидации он нужен
        super().run_validators(f"+{value}")

    def to_representation(self, value):
        return phone_utils.after_read_from_db(value)

