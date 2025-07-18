from django.urls import path

from .views import IndexView, LoginView, LogoutView, LogoutConfirm

app_name = 'home'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout/confirm', LogoutConfirm.as_view(), name='logout_confirm')
]
