# comite_pro/bancos/urls.py

from django.urls import path
from .views import DocumentoBancoListView, RegistroDocumentoBancoView
from . import views

urlpatterns = [
    path('', DocumentoBancoListView.as_view(), name='documentobanco_list'),
    path('crear/', RegistroDocumentoBancoView.as_view(), name='documentobanco_create'),
    path('editar/<int:pk>/', views.EditarDocumentoBancoView.as_view(), name='documentobanco_edit'),
]
