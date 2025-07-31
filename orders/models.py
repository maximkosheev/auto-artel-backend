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
    phone = models.CharField(unique=True, help_text='Телефон для связи', null=True)
    telegram_id = models.BigIntegerField(editable=False, null=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_by_telegram_id(value):
        return Client.objects.get(telegram_id=value)

    @staticmethod
    def get_by_phone(value):
        return Client.objects.get(phone=value)


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
    CLIENT_STATUS_CHOICES = [
        ('ASSIGNED', 'Менеджер принял заказ в работу'),
        ('WAIT_APPROVAL', 'На согласовании с клиентом'),
        ('WAIT_PAYMENT', 'Ждет оплаты'),
        ('PAID', 'Оплачен'),
        ('WAIT_SEND', 'Ждет отправки у поставщиков'),
        ('DELIVERY', 'Отправлен'),
        ('READY', 'Ждет выдачи в ПВЗ'),
        ('FINISHED', 'Завершен')
    ]
    id = models.BigAutoField(primary_key=True)
    status = models.CharField(choices=STATUS_CHOICES, default='NEW')
    client_status = models.CharField(null=True, choices=CLIENT_STATUS_CHOICES)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    manager = models.ManyToManyField(Manager)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    initial_requirements = models.TextField()
