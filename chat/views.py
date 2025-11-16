from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import generic


def is_manager(user):
    return user.groups.filter(name='manager').exists()


class IsManagerMixin(UserPassesTestMixin):
    def test_func(self):
        return is_manager(self.request.user)


# Create your views here.
class ChatListView(IsManagerMixin, generic.ListView):
    pass


class ChatWithClient(IsManagerMixin, generic.DetailView):
    pass
