# comite_pro/transacciones/urls.py

from django.urls import path
from .views import (
    RegistrarPolizaView, 
    PolizaListView,
    ActualizarPolizaView
)

urlpatterns = [
    path('polizas/', PolizaListView.as_view(), name='poliza_list'),
    path('polizas/registrar_poliza/', RegistrarPolizaView.as_view(), name='registrar_poliza'),
    path('polizas/editar/<int:pk>/', ActualizarPolizaView.as_view(), name='editar_poliza'),
]
