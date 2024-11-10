# comite_pro/documentos/forms.py

from django import forms
from .models import TipoDocumento, DocComprobante

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
        fields = ['empresa', 'tipo_documento', 'descripcion', 'numero_documento', 'serie_documento', 'fecha', 'monto_total', 'estado']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
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

        # Validar que la empresa y la fecha sean válidas
        if not empresa:
            self.add_error('empresa', 'Debe seleccionar una empresa.')

        if not fecha:
            self.add_error('fecha', 'Debe ingresar una fecha.')
        
        return cleaned_data
