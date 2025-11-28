import random
import secrets
import string

from django.contrib.auth.models import User, Group
from django.core.management import BaseCommand

from orders.models import Client, Manager


class Command(BaseCommand):
    help = 'Create test data: clients, managers, vehicle, orders, chat messages etc.'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.client_group = Group.objects.get_by_natural_key('client')
        self.manager_group = Group.objects.get_by_natural_key('manager')

    def handle(self, *args, **options):
        test_client1 = self._create_test_client('test_client1')
        test_manager1 = self._create_test_manager('test_manager1')

    def _create_test_client(self, client_name):
        self.stdout.write(
            self.style.SUCCESS(f'Creating test client... {client_name}')
        )
        phone_digits = '0123456789'
        client_user = self._create_test_user(client_name, self.client_group)
        client = Client.objects.create(
            user=client_user,
            name=client_name,
            phone='7' + ''.join(random.choices(phone_digits, k=10))
        )
        client.save()
        self.stdout.write(self.style.SUCCESS('Created'))
        return client

    def _create_test_manager(self, manager_name):
        self.stdout.write(
            self.style.SUCCESS(f'Creating test manager... {manager_name}')
        )
        phone_digits = '0123456789'
        client_user = self._create_test_user(manager_name, self.manager_group)
        client = Manager.objects.create(
            user=client_user,
            name=manager_name,
            phone='7' + ''.join(random.choices(phone_digits, k=10))
        )
        client.save()
        self.stdout.write(self.style.SUCCESS('Created'))
        return client

    def _create_test_user(self, user_name, group):
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        user = User.objects.create_user(username=user_name, password=password, email=f"{user_name}@auto-artel.com")
        user.groups.add(group)
        user.save()
        return user
