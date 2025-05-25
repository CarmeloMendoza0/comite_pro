#comite_pro/empresa/urls.py
from django.urls import path
from .views import EmpresaFormView, PeriodoContableCreateView, PeriodoContableListView, EmpresasListView, EmpresaUpdateView, CambiarEstadoPeriodoView, DashboardView

urlpatterns = [
    # dashboard 
    path('', DashboardView.as_view(), name='dashboard'),
    # URLs para empresas
    path('emp', EmpresasListView.as_view(), name="empresa_list"),
    path('crear/', EmpresaFormView.as_view(), name="empresa_create"),
    path('editar/<int:pk>/', EmpresaUpdateView.as_view(), name='empresa_update'),
    path('cambiar_estado/<int:pk>/', CambiarEstadoPeriodoView.as_view(), name='cambiar_estado_periodo'),
    # URLs para periodos
    path('periodos', PeriodoContableListView.as_view(), name="lista_periodos"),
    path('agregar/', PeriodoContableCreateView.as_view(), name="agg_periodo_contable"),
]