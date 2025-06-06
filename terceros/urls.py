# comite_pro/terceros/urls.py
from django.urls import path
from .views import (
    ProveedorCreateView, ProveedorUpdateView, ProveedorListView, ProveedorDeleteView,
    ClienteCreateView, ClienteUpdateView, ClienteListView, ClienteDeleteView,
    DonanteCreateView, DonanteUpdateView, DonanteListView, DonanteDeleteView,
)

urlpatterns = [
    # Rutas para Proveedores
    path('proveedores/', ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/crear/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', ProveedorDeleteView.as_view(), name='proveedor_delete'), 

    # Clientes
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/crear/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', ClienteDeleteView.as_view(), name='cliente_delete'),  
    
    # Donantes
    path('donantes/', DonanteListView.as_view(), name='donante_list'),
    path('donantes/crear/', DonanteCreateView.as_view(), name='donante_create'),
    path('donantes/<int:pk>/editar/', DonanteUpdateView.as_view(), name='donante_update'),
    path('donantes/<int:pk>/eliminar/', DonanteDeleteView.as_view(), name='donante_delete'),  
]
