import re
from django import forms

from orders.models import Client, Manager
from utils import phone_utils


def phone_validator(value):
    if not phone_utils.validate(value):
        raise forms.ValidationError("Телефон не соответствует формату")


class PhoneNumberField(forms.CharField):
    def prepare_value(self, value):
        return phone_utils.after_read_from_db(value)


class ClientForm(forms.ModelForm):
    phone = PhoneNumberField(label='Телефон', help_text='Телефон в формате "+7XXXXXXXXXX"', validators=[phone_validator])

    class Meta:
        model = Client
        labels = {
            "user": "Пользователь",
            "name": "Имя"
        }
        fields = ['user', 'name']

    def clean_phone(self):
        data = self.cleaned_data['phone']
        return phone_utils.before_save_to_db(data)

    def save(self, commit=True):
        client = super(ClientForm, self).save(commit)

        if commit:
            client.save()

        return client


class ManagerForm(forms.ModelForm):
    phone = forms.CharField(label='Телефон', help_text='Телефон в формате "+7XXXXXXXXXX"', validators=[phone_validator])

    class Meta:
        model = Manager
        labels = {
            "user": "Пользователь",
            "name": "Имя"
        }
        fields = ['user', 'name']

    def save(self, commit=True):
        manager = super(ManagerForm, self).save(commit)

        if commit:
            manager.save()

        return manager
