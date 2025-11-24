from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q, Max
from django.shortcuts import render
from django.views import generic

from orders.models import Client


def is_manager(user):
    return user.groups.filter(name='manager').exists()


class IsManagerMixin(UserPassesTestMixin):
    def test_func(self):
        return is_manager(self.request.user)


class ChatListView(IsManagerMixin, generic.TemplateView):
    template_name = "chat/clients.html"

    def get(self, request, *args, **kwargs):
        client_name = request.GET.get('search')
        where = Q(name__icontains=client_name) if client_name is not None else Q()

        clients = (Client.objects.annotate(
            unread_count=Count(
                'chatmessage',
                filter=Q(chatmessage__manager_id__isnull=True, chatmessage__viewed=False)),
            last_message_time=Max('chatmessage__created'))
                   .filter(where)
                   .order_by('-unread_count', '-last_message_time'))
        return render(request, self.template_name, {
            'clients': clients
        })


class ChatWithClient(IsManagerMixin, generic.DetailView):
    pass
