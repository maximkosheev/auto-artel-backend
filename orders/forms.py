from django import forms

from .models import Order


class OrderNewForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['initial_requirements']
        widgets = {
            'initial_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'readonly': True,
                'rows': 4,
                'placeholder': 'Пожелания клиента'
            }),
        }
        labels = {
            'initial_requirements': 'Исходные требования клиента'
        }


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
