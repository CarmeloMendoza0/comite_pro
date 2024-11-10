# comite_pro/transacciones/urls.py

from django.urls import path
from .views import (
    RegistrarComprobanteView, 
    RegistrarPolizaView, 
    PolizaListView,
    ActualizarPolizaView
)

urlpatterns = [
    path('registrar/', RegistrarComprobanteView.as_view(), name='registrar_comprobante'),
    path('polizas/', PolizaListView.as_view(), name='poliza_list'),
    path('polizas/registrar_poliza/', RegistrarPolizaView.as_view(), name='registrar_poliza'),
    path('polizas/editar/<int:pk>/', ActualizarPolizaView.as_view(), name='editar_poliza'),
]
