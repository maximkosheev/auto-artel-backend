import re
from django import forms

from orders.models import Client, Manager


def phone_validator(value):
    pattern = re.compile("^\\+7\\d{10}$",
                         re.RegexFlag.M)
    if not re.match(pattern, value):
        raise forms.ValidationError("Телефон не соответствует формату")


class ClientForm(forms.ModelForm):
    phone = forms.CharField(label='Телефон', help_text='Телефон в формате "+7XXXXXXXXXX"', validators=[phone_validator])

    class Meta:
        model = Client
        labels = {
            "user": "Пользователь",
            "name": "Имя"
        }
        fields = ['user', 'name']

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
