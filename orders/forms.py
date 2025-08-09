from django import forms
from django.forms import inlineformset_factory

from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['initial_requirements']
        widgets = {
            'initial_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Пожелания клиента'
            }),
        }
        labels = {
            'client': 'Клиент',
            'initial_requirements': 'Исходные требования клиента'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['client_display'] = forms.CharField(
                initial=self.instance.client,
                widget=forms.TextInput(attrs={
                    'readonly': True,
                    'class': 'form-control',
                    'style': 'background-color: #f8f9fa;'
                }),
                label='Клиент',
                required=False)


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['article_number', 'manufacture', 'name', 'price']
        widgets = {
            'article_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Артикул'
            }),
            'manufacture': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Производитель'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наименование'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }
        labels = {
            'article_number': 'Артикул',
            'manufacture': 'Производитель',
            'name': 'Наименование',
            'price': 'Цена'
        }


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,  # Number of empty forms to display
    can_delete=True,
    min_num=0,
    validate_min=False
)
