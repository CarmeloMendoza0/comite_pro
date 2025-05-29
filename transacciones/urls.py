# comite_pro/transacciones/urls.py

from django.urls import path
from .views import (
    RegistrarPolizaView, 
    PolizaListView,
    ActualizarPolizaView,
    EliminarPolizaView,
    verificar_credencial_admin  
)

urlpatterns = [
    path('polizas/', PolizaListView.as_view(), name='poliza_list'),
    path('polizas/registrar_poliza/', RegistrarPolizaView.as_view(), name='registrar_poliza'),
    path('polizas/editar/<int:pk>/', ActualizarPolizaView.as_view(), name='editar_poliza'),
    path('polizas/eliminar/<int:pk>/', EliminarPolizaView.as_view(), name='eliminar_poliza'),
    path('verificar-credencial-admin/', verificar_credencial_admin, name='verificar_credencial_admin'),
]
