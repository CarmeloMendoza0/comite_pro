# comite_pro/bancos/models.py

from django.db import models
from empresa.models import Empresa
from documentos.models import TipoDocumento
from terceros.models import Persona, Proveedor

class DocumentoBanco(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentos_banco', verbose_name="Empresa")
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.RESTRICT, related_name='documentos_banco', verbose_name="Tipo de Documento")
    entidad = models.ForeignKey(Persona, on_delete=models.SET_NULL, blank=True, null=True, related_name='documentos_banco', verbose_name="Entidad")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, blank=True, null=True, related_name='documentos_banco', verbose_name="Proveedor")
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Número del Documento:")
    fecha = models.DateField(verbose_name="Fecha")
    monto = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto")

    def __str__(self):
        return f"{self.numero_documento} - {self.tipo_documento.nombre} - {self.monto}"
