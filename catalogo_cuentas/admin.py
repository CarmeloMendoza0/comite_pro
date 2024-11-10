from django.contrib import admin
from .models import CatalogoCuentas, Cuenta
# Registrar los modelos en el administrador
admin.site.register(CatalogoCuentas)
admin.site.register(Cuenta)
