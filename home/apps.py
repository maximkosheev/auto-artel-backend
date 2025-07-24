from django.apps import AppConfig
from django.db.models.signals import post_migrate


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        post_migrate.connect(self.initialize, sender=self)

    def initialize(self, **kwargs):
        from django.contrib.auth.models import User, Group

        def create_groups():
            api_group = Group(name='api')
            manager_group = Group(name='manager')
            client_group = Group(name='client')

            Group.objects.bulk_create(objs=[api_group, manager_group, client_group], ignore_conflicts=True)

        def create_api_user():
            api_group = Group.objects.get(name='api')
            if not User.objects.filter(username='auto_artel_bot').exists():
                api_user = User.objects.create_user(username='auto_artel_bot', email=None, password='xxx')
                api_user.groups.add(api_group)
                api_user.save()

        create_groups()
        create_api_user()
