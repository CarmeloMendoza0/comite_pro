from django.urls import path
from .views import (
    TipoDocumentoListView, TipoDocumentoCreateView, TipoDocumentoUpdateView,
    DocComprobanteListView, RegistroDocComprobanteView, EditarDocComprobanteView
)

urlpatterns = [
    # URLs para TipoDocumento
    path('', TipoDocumentoListView.as_view(), name='tipodocumento_list'),
    path('crear/', TipoDocumentoCreateView.as_view(), name='tipodocumento_create'),
    path('editar/<int:pk>/', TipoDocumentoUpdateView.as_view(), name='tipodocumento_update'),
    
    # URLs para DocComprobante
    path('comprobantes/', DocComprobanteListView.as_view(), name='doccomprobante_list'),
    path('comprobantes/crear/', RegistroDocComprobanteView.as_view(), name='doccomprobante_create'),
    path('comprobantes/editar/<int:pk>/', EditarDocComprobanteView.as_view(), name='doccomprobante_update'),
]