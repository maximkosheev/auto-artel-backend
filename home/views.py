from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LogoutView as BaseLogoutView,
)
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import never_cache

from .forms import (
    LoginForm
)


class IndexView(generic.TemplateView):
    template_name = 'home/index.html'


class GuestOnlyView(generic.View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)


class LoginView(GuestOnlyView, generic.FormView):
    form_class = LoginForm
    template_name = "home/login.html"

    def form_valid(self, form):
        request = self.request
        login(request, form.user_cache)
        redirect_to = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME))
        if redirect_to is None:
            redirect_to = '/'
        return redirect(redirect_to)

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)


class LogoutConfirm(LoginRequiredMixin, generic.TemplateView):
    template_name = "home/logout_confirm.html"


class LogoutView(LoginRequiredMixin, BaseLogoutView):
    template_name = "home/logout.html"

