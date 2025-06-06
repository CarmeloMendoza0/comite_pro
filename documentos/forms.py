# comite_pro/documentos/forms.py

from django import forms

from terceros.models import Persona, Proveedor
from .models import TipoDocumento, DocComprobante
from django.core.exceptions import ValidationError
from transacciones.models import Movimiento, Transaccion

class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['nombre', 'descripcion', 'tipo', 'codigo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-input'}),
        }

class DocComprobanteForm(forms.ModelForm):
    class Meta:
        model = DocComprobante
        fields = ['empresa', 'tipo_documento', 'cliente', 'proveedor', 'descripcion', 'numero_documento', 'serie_documento', 'fecha', 'monto_total', 'estado']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-input'}), 
            'numero_documento': forms.TextInput(attrs={'class': 'form-input'}),
            'serie_documento': forms.TextInput(attrs={'class': 'form-input'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'monto_total': forms.NumberInput(attrs={'class': 'form-input'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        is_edit = kwargs.pop('is_edit', False)  # ← AGREGAR
        super().__init__(*args, **kwargs)
        
        if not is_edit:
            # Para nuevos registros, mostrar solo clientes y proveedores activos
            self.fields['cliente'].queryset = Persona.objects.filter(
                activo=True, tipo=Persona.CLIENTE
            )
            self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
            self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(
                activo=True, tipo='Comprobante'
            )
        else:
            # Para edición, mostrar todos pero marcar los inactivos
            # Clientes
            cliente_choices = []
            for cliente in Persona.objects.filter(tipo=Persona.CLIENTE):
                label = str(cliente) if cliente.activo else f"{cliente} (INACTIVO)"
                cliente_choices.append((cliente.id, label))
            self.fields['cliente'].choices = [('', '---------')] + cliente_choices
            # Proveedores
            proveedor_choices = []
            for proveedor in Proveedor.objects.all():
                label = str(proveedor) if proveedor.activo else f"{proveedor} (INACTIVO)"
                proveedor_choices.append((proveedor.id, label))
            self.fields['proveedor'].choices = [('', '---------')] + proveedor_choices
            # TipoDocumento
            tipo_documento_choices = []
            for tipo_doc in TipoDocumento.objects.filter(tipo='Comprobante'):
                label = str(tipo_doc) if tipo_doc.activo else f"{tipo_doc} (INACTIVO)"
                tipo_documento_choices.append((tipo_doc.id, label))
            self.fields['tipo_documento'].choices = [('', '---------')] + tipo_documento_choices

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        fecha = cleaned_data.get('fecha')
        cliente = cleaned_data.get('cliente')
        proveedor = cleaned_data.get('proveedor')
        tipo_documento = cleaned_data.get('tipo_documento')

        # Validar que la empresa y la fecha sean válidas
        if not empresa:
            self.add_error('empresa', 'Debe seleccionar una empresa.')

        if not fecha:
            self.add_error('fecha', 'Debe ingresar una fecha.')
        
        # Validar que no se seleccionen cliente y proveedor simultáneamente
        if cliente and proveedor:
            self.add_error('cliente', 'No puede seleccionar un cliente y un proveedor al mismo tiempo.')
            self.add_error('proveedor', 'No puede seleccionar un cliente y un proveedor al mismo tiempo.')
        
        # Validación específica según el tipo de documento
        if tipo_documento:
            if tipo_documento.tipo == 'Venta' and not cliente:
                self.add_error('cliente', 'Debe seleccionar un cliente para documentos de venta.')
            elif tipo_documento.tipo == 'Compra' and not proveedor:
                self.add_error('proveedor', 'Debe seleccionar un proveedor para documentos de compra.')
        
        return cleaned_data

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['cuenta', 'debe', 'haber']
        widgets = {
            'cuenta': forms.Select(attrs={'class': 'form-select'}),
            'debe': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-input'}),
            'haber': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        debe = cleaned_data.get('debe') or 0
        haber = cleaned_data.get('haber') or 0
        
        # Validar que solo se ingrese un valor en debe o en haber
        if debe > 0 and haber > 0:
            raise ValidationError('No puede ingresar valores en Debe y Haber simultáneamente.')
        if debe == 0 and haber == 0 and not self.cleaned_data.get('DELETE', False):
            raise ValidationError('Debe ingresar un valor en Debe o en Haber.')
            
        return cleaned_data

# FormSet para manejar múltiples movimientos en una transacción
MovimientoFormSet = forms.inlineformset_factory(
    Transaccion,     # Modelo padre
    Movimiento,      # Modelo hijo
    form=MovimientoForm,
    extra=0,         # No añadir formularios extra por defecto 
    can_delete=True, # Permitir eliminar movimientos
    #min_num=1,       # Mínimo un movimiento
    #validate_min=True,
)