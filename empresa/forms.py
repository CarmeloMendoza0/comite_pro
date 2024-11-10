from django import forms 
from django.contrib.auth.models import User
from .models import Empresa, PeriodoContable

class EmpresaForm(forms.ModelForm):
    usuarios = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple, #para seleccionar usuarios selector
        required=False,
        label="Usuarios"
    )

    class Meta:
        model = Empresa
        fields = ['rtu', 'razon_social', 'giro', 'direccion', 'telefono', 'usuarios']

class PeriodoContableForm(forms.ModelForm):
    class Meta:
        model = PeriodoContable
        fields = ['empresa', 'fecha_inicio', 'fecha_fin', 'estado']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }
