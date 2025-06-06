#comite_pro/documentos/urls.py
from django.urls import path
from .views import (
    TipoDocumentoListView, TipoDocumentoCreateView, TipoDocumentoUpdateView, TipoDocumentoDeleteView,
    DocComprobanteListView, RegistroDocComprobanteView, EditarDocComprobanteView,
    EliminarDocComprobanteView, verificar_credencial_admin
)

urlpatterns = [
    # URLs para TipoDocumento
    path('', TipoDocumentoListView.as_view(), name='tipodocumento_list'),
    path('crear/', TipoDocumentoCreateView.as_view(), name='tipodocumento_create'),
    path('editar/<int:pk>/', TipoDocumentoUpdateView.as_view(), name='tipodocumento_update'),
    path('eliminar/<int:pk>/', TipoDocumentoDeleteView.as_view(), name='tipodocumento_delete'),
    
    # URLs para DocComprobante
    path('comprobantes/', DocComprobanteListView.as_view(), name='doccomprobante_list'),
    path('comprobantes/crear/', RegistroDocComprobanteView.as_view(), name='doccomprobante_create'),
    path('comprobantes/editar/<int:pk>/', EditarDocComprobanteView.as_view(), name='doccomprobante_update'),
    path('comprobantes/eliminar/<int:pk>/', EliminarDocComprobanteView.as_view(), name='doccomprobante_delete'),
    path('verificar-credencial-admin/', verificar_credencial_admin, name='verificar_credencial_admin'),
]

