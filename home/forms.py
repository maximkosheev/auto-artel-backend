from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class UserCacheMixin:
    user_cache = None


class LoginForm(UserCacheMixin, forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    remember_me = forms.BooleanField(label="Remember me", required=False)

    def clean(self):
        username = self.cleaned_data["username"]
        password = self.cleaned_data["password"]

        user = User.objects.filter(username=username).first()

        if not user or not user.is_active or not user.check_password(password):
            raise ValidationError(f"Пара логин/пароль не найдена или пользователь заблокирован")

        self.user_cache = user
