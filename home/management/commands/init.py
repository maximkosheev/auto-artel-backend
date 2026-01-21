import os

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create required groups and users'

    def handle(self, *args, **options):
        api_group = self._create_group('api')
        manager_group = self._create_group('manager')
        client_group = self._create_group('client')
        self._assign_group_permissions(manager_group, 'add_session')
        self._create_user(name='auto_artel_bot', group=api_group)

    def _create_group(self, name):
        group, create = Group.objects.get_or_create(name=name)

        if create:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {name} group')
            )
        return group

    def _assign_group_permissions(self, group, permission_codename):
        try:
            permission = Permission.objects.get(codename=permission_codename)
            group.permissions.add(permission)
            group.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully assign {permission_codename} to group {group.name}')
            )
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Permission {permission_codename} not found')
            )

    def _create_user(self, name, group):
        name_env = name.upper()
        user_pass_env = os.getenv(name_env + '_PASSWORD')
        user_email_env = os.getenv(name_env + '_EMAIL')

        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            user = User.objects.create_user(username=name, password=user_pass_env, email=user_email_env)

        user.groups.add(group)
        user.save()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {name} user')
        )
        return user

