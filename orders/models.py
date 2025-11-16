from django.conf import settings
from django.db import models
from django.utils import timezone


def vin_validator(value):
    # raise ValidationError if vin number is not valid
    pass


class Vehicle(models.Model):
    vin = models.CharField(unique=True, null=True, validators=[vin_validator])
    manufacture = models.CharField(help_text='Производитель')
    model = models.CharField(help_text='Модель')
    year = models.IntegerField(help_text='Год выпуска')
    client = models.ForeignKey('Client', related_name='vehicle_list', on_delete=models.RESTRICT)


class Client(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    name = models.CharField(help_text='Фамилия Имя Отчество')
    phone = models.CharField(unique=True, help_text='Телефон для связи')
    telegram_id = models.BigIntegerField(null=True, unique=True)

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
    phone = models.CharField(help_text='Телефон для связи в формате +7XXXXXXXXXX')

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('CANCELLED', 'Отменен'),
        ('PROCESSING', 'В работе'),
        ('COMPLETED', 'Завершен')
    ]
    CLIENT_STATUS_CHOICES = [
        ('NOT_ASSIGNED', 'Новый'),
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
    client_status = models.CharField(null=True, choices=CLIENT_STATUS_CHOICES, default='NOT_ASSIGNED')
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    manager = models.ForeignKey(Manager, null=True, on_delete=models.PROTECT)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    initial_requirements = models.TextField()


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    article_number = models.CharField(null=True, help_text='Артикул')
    manufacture = models.CharField(null=True, help_text='Производитель')
    name = models.CharField(null=True, help_text='Наименование')
    price = models.DecimalField(null=True, max_digits=19, decimal_places=2, help_text='Стоимость')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_item_list')
