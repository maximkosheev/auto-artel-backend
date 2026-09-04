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
    internal_name = models.CharField(help_text='Дополнительное имя, назначается администратором', null=True)
    phone = models.CharField(unique=True, help_text='Телефон для связи')
    telegram_id = models.BigIntegerField(null=True, unique=True)

    class Meta:
        ordering = ["name", "-phone"]

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
    class Statuses(models.TextChoices):
        NEW = 'NEW', 'Новый'
        CANCELED = ('CANCELLED', 'Отменен')
        PROCESSING = ('PROCESSING', 'В работе')
        COMPLETED = ('COMPLETED', 'Завершен')

    class ClientStatuses(models.TextChoices):
        NOT_ASSIGNED = ('NOT_ASSIGNED', 'Новый')
        CANCELED = ('CANCELED', 'Отменен')
        ASSIGNED = ('ASSIGNED', 'В работе')
        WAIT_APPROVAL = ('WAIT_APPROVAL', 'На согласовании')
        APPROVED = ('APPROVED', 'Согласован')
        WAIT_PAYMENT = ('WAIT_PAYMENT', 'Ждет оплаты')
        PAID = ('PAID', 'Оплачен')
        WAIT_SEND = ('WAIT_SEND', 'Ждет отправки')
        DELIVERY = ('DELIVERY', 'Отправлен')
        READY = ('READY', 'Ждет выдачи в ПВЗ')
        FINISHED = ('FINISHED', 'Завершен')
    id = models.BigAutoField(primary_key=True)
    status = models.CharField(choices=Statuses, default=Statuses.NEW)
    client_status = models.CharField(null=True, choices=ClientStatuses, default=ClientStatuses.NOT_ASSIGNED)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    manager = models.ForeignKey(Manager, null=True, on_delete=models.PROTECT)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    initial_requirements = models.TextField()
    payment_link = models.CharField(null=True, help_text='Ссылка на оплату')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_status_changed = False

    def __str__(self):
        return f'Заказ #{self.id} ({self.status})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.client_status_changed = False

    @property
    def created_date(self):
        return self.created.date()

    def update_status(self, status: Statuses, commit: bool = False):
        self.status = status
        self.updated = timezone.now()
        if commit:
            self.save(update_fields=['status', 'updated'])

    def update_client_status(self, client_status: ClientStatuses, commit: bool = False):
        if self.client_status != client_status:
            self.client_status_changed = True
        self.client_status = client_status
        self.updated = timezone.now()
        if commit:
            self.save(update_fields=['client_status', 'updated'])

    def created_date_formatted(self, template: str | None = None):
        if self.created_date is not None:
            if template is not None:
                return self.created_date.strftime(template)
            else:
                return self.created_date.isoformat()
        return None


class OrderItem(models.Model):
    class Statuses(models.TextChoices):
        DEFAULT = 'DEFAULT', 'Не задан'
        AGREEMENT = 'AGREEMENT', 'На согласовании'
        APPROVED = 'APPROVED', 'Согласован клиентом'
        REJECTED = 'REJECTED', 'Отклонён клиентом'
        READY_FOR_ORDER = 'READY_FOR_ORDER', 'Готов к заказу'
        ORDERED = 'ORDERED', 'Заказан',
        HALF_ORDERED = 'HALF_ORDERED', 'Заказан частично'
        READY = 'READY', 'Ждет выдачи в ПВЗ'
    id = models.BigAutoField(primary_key=True)
    article_number = models.CharField(null=False, default='Артикул отсутствует', help_text='Артикул')
    manufacture = models.CharField(null=False, default='Производитель отсутствует', help_text='Производитель')
    name = models.CharField(null=False, default="Наименование отсутствует", help_text='Наименование')
    count = models.IntegerField(null=False, default=1, help_text='Количество')
    multiplicity = models.IntegerField(null=False, default=1, help_text='Кратность')
    status = models.CharField(choices=Statuses, default=Statuses.DEFAULT)
    price = models.DecimalField(null=False, max_digits=19, decimal_places=2, default=0.0, help_text='Цена')
    discount = models.DecimalField(null=False, max_digits=5, decimal_places=2, default=0.00,
                                   help_text='Скидка. 0 - 100% оплаты; 0.1 - скидка 10%')

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_item_list')
    confirmed = models.BooleanField(default=False, help_text='Признак, что данная позиция утверждена в заказе')

    provider = models.CharField(null=True, help_text='Поставщик, например, ArmTek')
    delivery_dt = models.DateTimeField(null=True, help_text='Дата поставки, заявленная поставщиком')
    warehouse = models.CharField(null=True, help_text='Склад поставщика')
    internal_id = models.CharField(null=True, help_text='Внутренний идентификатор запчасти у поставщика')
    purchase_price = models.DecimalField(null=True, max_digits=19, decimal_places=2,
                                         help_text='Цена у поставщица (цена закупки)')

    def client_short_str(self):
        return f"{self.name};{self.manufacture}; Кол-во:{self.count}; Цена:{self.price}"
