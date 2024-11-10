# comite_pro/bancos/models.py

from django.db import models
from empresa.models import Empresa
from documentos.models import TipoDocumento

class DocumentoBanco(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentos_banco')
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.RESTRICT, related_name='documentos_banco')
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Número del Documento:")
    fecha = models.DateField(verbose_name="Fecha")
    monto = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto")

    def __str__(self):
        return f"{self.numero_documento} - {self.tipo_documento.nombre} - {self.monto}"
