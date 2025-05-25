# comite_pro/documentos/forms.py

from django import forms
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