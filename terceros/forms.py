# comite_pro/terceros/forms.py
from django import forms
from .models import Proveedor, Persona

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['empresa', 'nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección del cliente'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = Persona.CLIENTE
        if commit:
            instance.save()
        return instance

class DonanteForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['empresa', 'nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del donante'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección del donante'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = Persona.DONANTE
        if commit:
            instance.save()
        return instance

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['empresa', 'nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
