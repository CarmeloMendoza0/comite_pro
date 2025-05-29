# comite_pro/bancos/urls.py

from django.urls import path
from .views import DocumentoBancoListView, RegistroDocumentoBancoView, EditarDocumentoBancoView, EliminarDocumentoBancoView, verificar_credencial_admin

urlpatterns = [
    path('', DocumentoBancoListView.as_view(), name='documentobanco_list'),
    path('crear/', RegistroDocumentoBancoView.as_view(), name='documentobanco_create'),
    path('editar/<int:pk>/', EditarDocumentoBancoView.as_view(), name='documentobanco_edit'),
    path('eliminar/<int:pk>/', EliminarDocumentoBancoView.as_view(), name='documentobanco_delete'),
    path('verificar-credencial/', verificar_credencial_admin, name='verificar_credencial_admin'),
]
