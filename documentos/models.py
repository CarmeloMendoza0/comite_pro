# comite_pro/documentos/models.py
from django.db import models
from django.forms import ValidationError
from empresa.models import Empresa
from terceros.models import Proveedor
from terceros.models import Persona, Proveedor

class TipoDocumento(models.Model):
    TIPO_CHOICES = [
        ('Comprobante', 'Comprobante'),
        ('Póliza', 'Póliza'),
        ('Documento Bancario', 'Documento Bancario'),
    ]

    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    activo = models.BooleanField(default=True, verbose_name="Activo",
                                help_text="Indica si está activo en el sistema")

    def __str__(self):
        estado_str = " (INACTIVO)" if not self.activo else ""
        return f"{self.codigo} - {self.nombre}{estado_str}"
    
    def desactivar(self):
        """Método para desactivar el tipo de documento de forma controlada"""
        self.activo = False
        self.save()

    def activar(self): 
        """Método para reactivar el tipo de documento si es necesario"""
        self.activo = True
        self.save()

    # Managers personalizados para filtrar tipos
    @classmethod 
    def activos(cls):
        """Retorna solo tipos de documento activos"""
        return cls.objects.filter(activo=True)

    @classmethod 
    def inactivos(cls):
        """Retorna solo tipos de documento inactivos"""
        return cls.objects.filter(activo=False)

class DocComprobante(models.Model):
    ESTADO_CHOICES = [
        ('Emitido', 'Emitido'),
        ('Pagado', 'Pagado'),
        ('Anulado', 'Anulado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, related_name='documentos')
    cliente = models.ForeignKey(Persona, on_delete=models.SET_NULL, blank=True, null=True, related_name='comprobantes', verbose_name="Cliente")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, blank=True, null=True, related_name='comprobantes', verbose_name="Proveedor")
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción")
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Documento")
    serie_documento = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Serie")
    fecha = models.DateField(verbose_name="Fecha")
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Emitido')
    activo = models.BooleanField(default=True, verbose_name="Activo", help_text="Indica si el documento está activo en el sistema")

    def __str__(self):
        estado_str = " (INACTIVO)" if not self.activo else ""
        return f"{self.numero_documento} - {self.tipo_documento.nombre}{estado_str}"
    
    def clean(self):
    # Validar que el monto total sea positivo
        if self.monto_total <= 0:
            raise ValidationError('El monto total debe ser mayor que cero.')
        
    def desactivar(self):
        """Método para desactivar el documento de forma controlada"""
        self.activo = False
        self.save()
    
    def activar(self):
        """Método para reactivar el documento si es necesario"""
        self.activo = True
        self.save()

    # Managers personalizados para filtrar documentos
    @classmethod
    def activos(cls):
        """Retorna solo documentos activos"""
        return cls.objects.filter(activo=True)
    
    @classmethod
    def inactivos(cls):
        """Retorna solo documentos inactivos"""
        return cls.objects.filter(activo=False)



