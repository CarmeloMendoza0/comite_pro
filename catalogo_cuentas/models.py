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
    activo = models.BooleanField(default=True, verbose_name="Activo", 
                                help_text="Indica si está activo en el sistema")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        estado_str = " (INACTIVO)" if not self.activo else ""
        return f"{self.nombre} ({self.empresa.razon_social}){estado_str}"
    
    def desactivar(self):
        """Método para desactivar el catálogo de forma controlada"""
        self.activo = False
        self.save()
    
    def activar(self):
        """Método para reactivar el catálogo si es necesario"""
        self.activo = True
        self.save()

    # Managers personalizados para filtrar catálogos
    @classmethod
    def activos(cls):
        """Retorna solo catálogos activos"""
        return cls.objects.filter(activo=True)
    
    @classmethod
    def inactivos(cls):
        """Retorna solo catálogos inactivos"""
        return cls.objects.filter(activo=False)

class Cuenta(models.Model):
    catalogo = models.ForeignKey(CatalogoCuentas, on_delete=models.CASCADE, related_name='cuentas')
    nombre = models.CharField(max_length=100, verbose_name="nombre")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="código")
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="saldo")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcuentas')
    nivel = models.PositiveIntegerField(default=1, verbose_name="nivel")
    activo = models.BooleanField(default=True, verbose_name="Activo", 
                                help_text="Indica si está activa en el sistema")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        estado_str = " (INACTIVA)" if not self.activo else ""
        return f"{self.codigo} - {self.nombre}{estado_str}"
    
    def desactivar(self):
        """Método para desactivar la cuenta de forma controlada"""
        self.activo = False
        self.save()
    
    def activar(self):
        """Método para reactivar la cuenta si es necesario"""
        self.activo = True
        self.save()

    # Managers personalizados para filtrar cuentas
    @classmethod
    def activas(cls):
        """Retorna solo cuentas activas"""
        return cls.objects.filter(activo=True)
    
    @classmethod
    def inactivas(cls):
        """Retorna solo cuentas inactivas"""
        return cls.objects.filter(activo=False)
    
    def clean(self):
        if not CatalogoCuentas.objects.filter(id=self.catalogo_id).exists():
            raise ValidationError("El catálogo seleccionado no existe.")
