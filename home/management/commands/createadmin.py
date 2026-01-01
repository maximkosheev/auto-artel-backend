from django.contrib.auth.management.commands import createsuperuser
from django.contrib.auth.models import User


class Command(createsuperuser.Command):
    help = 'Create admin user'

    def handle(self, *args, **options):
        username = options.get('username')
        if not User.objects.filter(username=username).exists():
            super().handle(*args, **options)
        else:
            print(f"Superuser {username} already created")
