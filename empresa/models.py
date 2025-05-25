# comite_pro/empresa/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
class Empresa(models.Model):
    rtu = models.CharField(max_length=15, unique=True, verbose_name="rtu") 
    razon_social = models.CharField(max_length=200, unique=True, verbose_name="razón social")  
    giro = models.CharField(max_length=200, verbose_name="giro")  
    direccion = models.CharField(max_length=300, verbose_name="dirección") 
    telefono = models.CharField(max_length=20, verbose_name="teléfono")  
    usuario = models.ManyToManyField(User, related_name='empresa', blank=True)
    
    def __str__(self):
        return self.razon_social 

class PeriodoContable(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='periodos')
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    estado = models.CharField(max_length=25, choices=[
        ('Abierto', 'Abierto'),
        ('Cerrado', 'Cerrado'),
    ], default='Abierto', verbose_name="Estado")

    def __str__(self):
        return f"{self.empresa.razon_social} - {self.fecha_inicio} a {self.fecha_fin}"
    
    def clean(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

    # Sobrescribir el método save para ejecutar las validaciones antes de guardar
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        