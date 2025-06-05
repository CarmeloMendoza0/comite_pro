# comite_pro/catalogo_cuentas/forms.py

from django import forms
from .models import CatalogoCuentas, Cuenta

class CatalogoCuentasForm(forms.ModelForm):
    class Meta:
        model = CatalogoCuentas
        fields = ['empresa', 'nombre', 'tipo']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['catalogo', 'nombre', 'codigo', 'saldo', 'parent', 'nivel']
        widgets = {
            'catalogo': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'codigo': forms.TextInput(attrs={'class': 'form-input'}),
            'saldo': forms.NumberInput(attrs={'class': 'form-input'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'nivel': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        catalogo_queryset = kwargs.pop('catalogo_queryset', None)
        super().__init__(*args, **kwargs)
        
        if catalogo_queryset is not None:
            self.fields['catalogo'].queryset = catalogo_queryset
