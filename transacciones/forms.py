# comite_pro/transacciones/forms.py

from django import forms

from documentos.models import TipoDocumento
from .models import Transaccion, Movimiento
from empresa.models import PeriodoContable
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

    def __init__(self, *args, **kwargs):
        # Filtrar solo periodos abiertos para nuevos registros
        is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        if not is_edit:
            # Para nuevos registros, mostrar solo periodos abiertos
            self.fields['periodo'].queryset = PeriodoContable.objects.filter(estado='Abierto')
        else:
            # Para edición, mostrar todos los periodos pero marcar los cerrados
            self.fields['periodo'].queryset = PeriodoContable.objects.all()
            # Personalizar las opciones para mostrar el estado
            choices = []
            for periodo in PeriodoContable.objects.all():
                if periodo.estado == 'Cerrado':
                    label = f"{periodo} (CERRADO)"
                else:
                    label = str(periodo)
                choices.append((periodo.id, label))
            self.fields['periodo'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        fecha = cleaned_data.get('fecha')
        tipo_operacion = cleaned_data.get('tipo_operacion')

        # Validar que el periodo haya sido seleccionado
        if not periodo:
            self.add_error('periodo', 'Por favor, seleccione un periodo contable.')
        else:
            # Validar que el periodo esté abierto (solo para nuevos registros)
            if hasattr(self, 'instance') and not self.instance.pk:  # Nuevo registro
                if periodo.estado != 'Abierto':
                    self.add_error('periodo', 'Solo puede seleccionar periodos abiertos para nuevos registros.')

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
    # la fecha al formato esperado por el input HTML
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-date'}),
        input_formats=['%Y-%m-%d']
    )

    class Meta:
        model = Transaccion
        fields = [
            'empresa', 'descripcion', 'fecha', 'periodo', 'tipo_operacion', 'tipo_documento', 'numero_poliza'
        ]
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-input'}),
            # La definición del widget para fecha se hace arriba
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_operacion': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_poliza': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Filtrar solo periodos abiertos para nuevos registros
        is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        if not is_edit:
            # Para nuevos registros, mostrar solo periodos abiertos
            self.fields['periodo'].queryset = PeriodoContable.objects.filter(estado='Abierto')
            self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(
                activo=True, tipo='Póliza'
            )
        else:
            # Para edición, mostrar todos los periodos pero marcar los cerrados
            self.fields['periodo'].queryset = PeriodoContable.objects.all()
            # Personalizar las opciones para mostrar el estado
            choices = []
            for periodo in PeriodoContable.objects.all():
                if periodo.estado == 'Cerrado':
                    label = f"{periodo} (CERRADO)"
                else:
                    label = str(periodo)
                choices.append((periodo.id, label))
            self.fields['periodo'].choices = choices
            # TipoDocumento
            tipo_documento_choices = []
            for tipo_doc in TipoDocumento.objects.filter(tipo='Póliza'):
                label = str(tipo_doc) if tipo_doc.activo else f"{tipo_doc} (INACTIVO)"
                tipo_documento_choices.append((tipo_doc.id, label))
            self.fields['tipo_documento'].choices = [('', '---------')] + tipo_documento_choices

    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        fecha = cleaned_data.get('fecha')

        # Validar que el periodo haya sido seleccionado
        if not periodo:
            self.add_error('periodo', 'Por favor, seleccione un periodo contable.')
        else:
            # Validar que el periodo esté abierto (solo para nuevos registros)
            if hasattr(self, 'instance') and not self.instance.pk:  # Nuevo registro
                if periodo.estado != 'Abierto':
                    self.add_error('periodo', 'Solo puede seleccionar periodos abiertos para nuevas pólizas.')

        # Validar que la fecha haya sido ingresada
        if not fecha:
            self.add_error('fecha', 'Por favor, ingrese una fecha.')
        else:
            # Validar que la fecha esté dentro del periodo
            if periodo and not (periodo.fecha_inicio <= fecha <= periodo.fecha_fin):
                self.add_error('fecha', 'La fecha debe estar dentro del periodo contable seleccionado.')
        
        return cleaned_data
