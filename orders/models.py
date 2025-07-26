from django.db import models
from django.utils import timezone
from django.conf import settings


def vin_validator(value):
    # raise ValidationError if vin number is not valid
    pass


class Vehicle(models.Model):
    vin = models.CharField(validators=[vin_validator])
    manufacture = models.CharField(help_text='Производитель')
    model = models.CharField(help_text='Модель')
    year = models.IntegerField(help_text='Год выпуска')
    client = models.ForeignKey('Client', on_delete=models.RESTRICT)


class Client(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    name = models.CharField(help_text='Фамилия Имя Отчество')
    phone = models.CharField(help_text='Телефон для связи')
    telegram_id = models.BigIntegerField(editable=False)


class Manager(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    name = models.CharField(help_text='Фамилия Имя Отчество')
    phone = models.CharField(help_text='Телефон для связи')


class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'new'),
        ('CANCELLED', 'cancelled'),
        ('PROCESSING', 'processing'),
        ('COMPLETED', 'completed')
    ]
    id = models.BigAutoField(primary_key=True)
    status = models.CharField(choices=STATUS_CHOICES, default='NEW')
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    manager = models.ManyToManyField(Manager)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    initial_requirements = models.TextField()
