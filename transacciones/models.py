
# comite_pro/transacciones/models.py
from django.db import models
from django.core.exceptions import ValidationError
from bancos.models import DocumentoBanco
from empresa.models import Empresa, PeriodoContable
from documentos.models import DocComprobante, TipoDocumento
from catalogo_cuentas.models import Cuenta

# Create your models here.
class Transaccion(models.Model):
    TIPO_TRANSACCION_CHOICES = [
        ('Ingreso', 'Ingreso'),
        ('Egreso', 'Egreso'),
    ]

    TIPO_POLIZA_CHOICES = [
        ('Transacción', 'Transacción'),
        ('Póliza', 'Póliza'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='transacciones')
    descripcion = models.CharField(max_length=255, verbose_name="Descripción")
    fecha = models.DateField(verbose_name="Fecha")
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Monto")
    tipo_transaccion = models.CharField(max_length=10, choices=TIPO_TRANSACCION_CHOICES, null=True, blank=True)
    periodo = models.ForeignKey(PeriodoContable, on_delete=models.CASCADE, related_name='transacciones')
    comprobante = models.ForeignKey(DocComprobante, on_delete=models.CASCADE, null=True, blank=True, related_name='transacciones')
    banco = models.ForeignKey(DocumentoBanco, on_delete=models.CASCADE, null=True, blank=True, related_name='transacciones')
    tipo_operacion = models.CharField(max_length=15, choices=TIPO_POLIZA_CHOICES, default='Transacción')
    numero_poliza = models.PositiveIntegerField(null=True, blank=True, verbose_name="Poliza")
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.descripcion} - {self.fecha}"
    
class Movimiento(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE, related_name='movimientos')
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='movimientos')
    debe = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    haber = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)

    def __str__(self):
        return f"{self.cuenta.codigo} - Debe: {self.debe} | Haber: {self.haber}"
            
    def clean(self):
        if (self.debe and self.haber) or (not self.debe and not self.haber):
            raise ValidationError('Debe ingresar un valor en Debe o en Haber, pero no en ambos.')