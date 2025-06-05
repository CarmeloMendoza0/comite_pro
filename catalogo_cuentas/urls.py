# comite_pro/catalogo_cuentas/urls.py

from django.urls import path
from .views import (
    CatalogoCuentasListView, CatalogoCuentasCreateView, CatalogoCuentasUpdateView, CatalogoCuentasDeleteView,
    CuentaListView, CuentaCreateView, CuentaUpdateView, CuentaDeleteView, PlanCuentasView
)

urlpatterns = [
    # URLs para CatalogoCuentas
    path('', CatalogoCuentasListView.as_view(), name='catalogo_list'),
    path('crear/', CatalogoCuentasCreateView.as_view(), name='catalogo_create'),
    path('editar/<int:pk>/', CatalogoCuentasUpdateView.as_view(), name='catalogo_update'),
    path('eliminar/<int:pk>/', CatalogoCuentasDeleteView.as_view(), name='catalogo_delete'),
    
    # URLs para Cuenta
    path('cuentas', CuentaListView.as_view(), name='cuenta_list'),
    path('cuentas/crear/', CuentaCreateView.as_view(), name='cuenta_create'),
    path('cuentas/editar/<int:pk>/', CuentaUpdateView.as_view(), name='cuenta_update'),
    path('cuentas/eliminar/<int:pk>/', CuentaDeleteView.as_view(), name='cuenta_delete'),

    # URL para Plan de Cuentas
    path('plan-cuentas/', PlanCuentasView.as_view(), name='plan_cuentas'),
]
