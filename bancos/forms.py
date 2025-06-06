# comite_pro/bancos/forms.py

from django import forms
from documentos.models import TipoDocumento
from terceros.models import Persona, Proveedor
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

    def __init__(self, *args, **kwargs):
        is_edit = kwargs.pop('is_edit', False)  # ← AGREGAR
        super().__init__(*args, **kwargs)
        
        if not is_edit:
            # Para nuevos registros, mostrar solo entidades y proveedores activos
            self.fields['entidad'].queryset = Persona.objects.filter(activo=True)
            self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
            self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(
                activo=True, tipo='Documento Bancario'
            )
        else:
            # Para edición, mostrar todos pero marcar los inactivos
            #Entidad
            entidad_choices = []
            for entidad in Persona.objects.all():
                label = str(entidad) if entidad.activo else f"{entidad} (INACTIVO)"
                entidad_choices.append((entidad.id, label))
            self.fields['entidad'].choices = [('', '---------')] + entidad_choices
            #Proveedor
            proveedor_choices = []
            for proveedor in Proveedor.objects.all():
                label = str(proveedor) if proveedor.activo else f"{proveedor} (INACTIVO)"
                proveedor_choices.append((proveedor.id, label))
            self.fields['proveedor'].choices = [('', '---------')] + proveedor_choices
            # TipoDocumento
            tipo_documento_choices = []
            for tipo_doc in TipoDocumento.objects.filter(tipo='Documento Bancario'):
                label = str(tipo_doc) if tipo_doc.activo else f"{tipo_doc} (INACTIVO)"
                tipo_documento_choices.append((tipo_doc.id, label))
            self.fields['tipo_documento'].choices = [('', '---------')] + tipo_documento_choices

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        fecha = cleaned_data.get('fecha')

        # Validar que la empresa y la fecha sean válidas
        if not empresa:
            self.add_error('empresa', 'Debe seleccionar una empresa.')

        if not fecha:
            self.add_error('fecha', 'Debe ingresar una fecha.')

        # validar algo más

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
