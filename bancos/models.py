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
    activo = models.BooleanField(default=True, verbose_name="Activo", 
                                help_text="Indica si el documento está activo en el sistema")
    
    def __str__(self):
        estado_str = " (INACTIVO)" if not self.activo else ""
        return f"{self.numero_documento} - {self.tipo_documento.nombre} - {self.monto}{estado_str}"
    
    def desactivar(self):
        """Método para desactivar el documento de forma controlada"""
        self.activo = False
        self.save()
    
    def activar(self):
        """Método para reactivar el documento si es necesario"""
        self.activo = True
        self.save()

    @classmethod
    def activos(cls):
        """Retorna solo documentos activos"""
        return cls.objects.filter(activo=True)
    
    @classmethod
    def inactivos(cls):
        """Retorna solo documentos inactivos"""
        return cls.objects.filter(activo=False)
