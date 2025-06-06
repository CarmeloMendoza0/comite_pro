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
    activo = models.BooleanField(default=True, verbose_name="Activo",
                                help_text="Indica si está activo en el sistema")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        estado_str = " (INACTIVO)" if not self.activo else ""
        return f"{self.get_tipo_display()}: {self.nombre}{estado_str}"
    def desactivar(self):
        """Método para desactivar la persona de forma controlada"""
        self.activo = False
        self.save()
    
    def activar(self):
        """Método para reactivar la persona si es necesario"""
        self.activo = True
        self.save()
    
    # Managers personalizados para filtrar personas
    @classmethod
    def activos(cls):
        """Retorna solo personas activas"""
        return cls.objects.filter(activo=True)
    
    @classmethod
    def inactivos(cls):
        """Retorna solo personas inactivas"""
        return cls.objects.filter(activo=False)

class Proveedor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='proveedores')
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name="Correo Electrónico")
    activo = models.BooleanField(default=True, verbose_name="Activo",
                                help_text="Indica si está activo en el sistema")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        estado_str = " (INACTIVO)" if not self.activo else ""
        return f"{self.nombre}{estado_str}" #return self.nombre
    
    def desactivar(self):
        """Método para desactivar el proveedor de forma controlada"""
        self.activo = False
        self.save()
    
    def activar(self):
        """Método para reactivar el proveedor si es necesario"""
        self.activo = True
        self.save()
    
    # Managers personalizados para filtrar proveedores
    @classmethod
    def activos(cls):
        """Retorna solo proveedores activos"""
        return cls.objects.filter(activo=True)
    
    @classmethod
    def inactivos(cls):
        """Retorna solo proveedores inactivos"""
        return cls.objects.filter(activo=False)


