# comite_pro/catalogo_cuentas/urls.py

from django.urls import path
from .views import (
    CatalogoCuentasListView, CatalogoCuentasCreateView, CatalogoCuentasUpdateView,
    CuentaListView, CuentaCreateView, CuentaUpdateView, PlanCuentasView
)

urlpatterns = [
    # URLs para CatalogoCuentas
    path('', CatalogoCuentasListView.as_view(), name='catalogo_list'),
    path('crear/', CatalogoCuentasCreateView.as_view(), name='catalogo_create'),
    path('editar/<int:pk>/', CatalogoCuentasUpdateView.as_view(), name='catalogo_update'),
    
    # URLs para Cuenta
    path('cuentas', CuentaListView.as_view(), name='cuenta_list'),
    path('cuentas/crear/', CuentaCreateView.as_view(), name='cuenta_create'),
    path('cuentas/editar/<int:pk>/', CuentaUpdateView.as_view(), name='cuenta_update'),

    # URL para Plan de Cuentas
    path('plan-cuentas/', PlanCuentasView.as_view(), name='plan_cuentas'),
]
