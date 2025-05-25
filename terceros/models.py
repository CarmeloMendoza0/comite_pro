# comite_pro/terceros/models.py
from django.db import models

# Create your models here.
from empresa.models import Empresa

class Persona(models.Model):
    CLIENTE = 'CL'
    DONANTE = 'DO'
    TIPO_CHOICES = [
        (CLIENTE, 'Cliente'),
        (DONANTE, 'Donante'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='personas')
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name="Correo Electrónico")
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, verbose_name="Tipo de Persona")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.nombre}"
    
class Proveedor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='proveedores')
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name="Correo Electrónico")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


