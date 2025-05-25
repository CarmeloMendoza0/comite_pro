# comite_pro/catalogo_cuentas/models.py

from django.db import models
from empresa.models import Empresa
from django.core.exceptions import ValidationError

class CatalogoCuentas(models.Model):
    TIPO_CATALOGO_CHOICES = [
        ('Activo', 'Activo'),
        ('Pasivo', 'Pasivo'),
        ('Capital', 'Capital'),
        ('Ingreso', 'Ingreso'),
        ('Egreso', 'Egreso'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='catalogos')
    nombre = models.CharField(max_length=100, verbose_name="nombre")
    tipo = models.CharField(max_length=10, choices=TIPO_CATALOGO_CHOICES, verbose_name="tipo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.empresa.razon_social})"

class Cuenta(models.Model):
    catalogo = models.ForeignKey(CatalogoCuentas, on_delete=models.CASCADE, related_name='cuentas')
    nombre = models.CharField(max_length=100, verbose_name="nombre")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="código")
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="saldo")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcuentas')
    nivel = models.PositiveIntegerField(default=1, verbose_name="nivel")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def clean(self):
        if not CatalogoCuentas.objects.filter(id=self.catalogo_id).exists():
            raise ValidationError("El catálogo seleccionado no existe.")
