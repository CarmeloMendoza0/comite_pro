# comite_pro/documentos/models.py
from django.db import models
from django.forms import ValidationError
from empresa.models import Empresa

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

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class DocComprobante(models.Model):
    ESTADO_CHOICES = [
        ('Emitido', 'Emitido'),
        ('Pagado', 'Pagado'),
        ('Anulado', 'Anulado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, related_name='documentos')
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción")
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Documento")
    serie_documento = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Serie")
    fecha = models.DateField(verbose_name="Fecha")
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Emitido')

    def __str__(self):
        return f"{self.numero_documento} - {self.tipo_documento.nombre}"
    
    def clean(self):
    # Validar que el monto total sea positivo
        if self.monto_total <= 0:
            raise ValidationError('El monto total debe ser mayor que cero.')



