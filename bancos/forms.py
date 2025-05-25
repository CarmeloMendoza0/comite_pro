# comite_pro/bancos/forms.py

from django import forms
from transacciones.models import Movimiento, Transaccion
from .models import DocumentoBanco

class DocumentoBancoForm(forms.ModelForm):
    class Meta:
        model = DocumentoBanco
        fields = ['empresa', 'tipo_documento','entidad', 'proveedor', 'numero_documento', 'fecha', 'monto']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'entidad': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-input'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'monto': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        fecha = cleaned_data.get('fecha')

        # Validar que la empresa y la fecha sean válidas
        if not empresa:
            self.add_error('empresa', 'Debe seleccionar una empresa.')

        if not fecha:
            self.add_error('fecha', 'Debe ingresar una fecha.')

        # Si necesitas validar algo más, hazlo aquí

        return cleaned_data

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['cuenta', 'debe', 'haber']
        widgets = {
            'cuenta': forms.Select(),
            'debe': forms.NumberInput(attrs={'step': '0.01'}),
            'haber': forms.NumberInput(attrs={'step': '0.01'}),
        }

MovimientoFormSet = forms.inlineformset_factory(
    Transaccion, 
    Movimiento, 
    form=MovimientoForm,
    extra=0,  # O el número que consideres adecuado
    can_delete=True,
)        
