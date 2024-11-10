# comite_pro/transacciones/forms.py

from django import forms
from .models import Transaccion, Movimiento
from django.forms import inlineformset_factory


class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = [
            'descripcion', 'fecha', 'monto_total', 'tipo_transaccion', 'periodo', 'tipo_operacion'
        ]
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-input'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-date'}),
            'monto_total': forms.NumberInput(attrs={'class': 'form-input'}),
            'tipo_transaccion': forms.Select(attrs={'class': 'form-select'}),
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_operacion': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        fecha = cleaned_data.get('fecha')
        tipo_operacion = cleaned_data.get('tipo_operacion')

        # Validar que el periodo haya sido seleccionado
        if not periodo:
            self.add_error('periodo', 'Por favor, seleccione un periodo contable.')
        else:
            # Validar que el periodo esté abierto
            if periodo.estado != 'Abierto':
                self.add_error('periodo', 'El periodo contable está cerrado.')

        # Validar que la fecha haya sido ingresada
        if not fecha:
            self.add_error('fecha', 'Por favor, ingrese una fecha.')
        else:
            # Validar que la fecha esté dentro del periodo
            if not (periodo.fecha_inicio <= fecha <= periodo.fecha_fin):
                self.add_error('fecha', 'La fecha debe estar dentro del periodo contable seleccionado.')
        
        if tipo_operacion == 'Transacción':
            if not cleaned_data.get('monto_total'):
                self.add_error('monto_total', 'Debe especificar el monto total para una transacción.')
            if not cleaned_data.get('tipo_transaccion'):
                self.add_error('tipo_transaccion', 'Debe seleccionar el tipo de transacción (Ingreso o Egreso).')
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

MovimientoFormSet = inlineformset_factory(
    Transaccion, 
    Movimiento, 
    form=MovimientoForm,
    extra=0, # Cambia a 0 para que no genere formularios vacíos automáticamente
    can_delete=True,
)

class PolizaForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = [
            'empresa', 'descripcion', 'fecha', 'periodo', 'tipo_operacion', 'tipo_documento', 'numero_poliza'
        ]
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-input'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-date'}),
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_operacion': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_poliza': forms.NumberInput(attrs={'class': 'form-input'}),
        }
