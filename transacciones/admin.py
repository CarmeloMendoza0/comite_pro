from django.contrib import admin
from .models import Transaccion, Movimiento

# Register your models here.
admin.site.register(Transaccion)
admin.site.register(Movimiento)