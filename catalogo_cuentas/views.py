# comite_pro/catalogo_cuentas/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from .models import CatalogoCuentas, Cuenta
from .forms import CatalogoCuentasForm, CuentaForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from comite_pro.utils import is_admin, is_accountant  # Importa las funciones
from django.core.paginator import Paginator

# Vistas para CatalogoCuentas

# Decorador aplicado para verificar si el usuario es administrador
@method_decorator(user_passes_test(is_admin), name='dispatch')
class CatalogoCuentasListView(LoginRequiredMixin, generic.ListView):
    model = CatalogoCuentas
    template_name = 'catalogo_cuentas/catalogo_list.html'
    context_object_name = 'catalogos'

@method_decorator(user_passes_test(is_admin), name='dispatch')
class CatalogoCuentasCreateView(LoginRequiredMixin, generic.CreateView):
    model = CatalogoCuentas
    form_class = CatalogoCuentasForm
    template_name = 'catalogo_cuentas/catalogo_form.html'
    success_url = reverse_lazy('catalogo_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Catálogo'
        return context
    
@method_decorator(user_passes_test(is_admin), name='dispatch')
class CatalogoCuentasUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = CatalogoCuentas
    form_class = CatalogoCuentasForm
    template_name = 'catalogo_cuentas/catalogo_form.html'
    success_url = reverse_lazy('catalogo_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Catálogo'
        return context

# Vistas para Cuenta

class CuentaListView(LoginRequiredMixin, generic.ListView):
    model = Cuenta
    template_name = 'catalogo_cuentas/cuenta_list.html'
    context_object_name = 'cuentas'
    paginate_by = 12  # Puedes ajustar este valor según tus necesidades

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(nombre__icontains=query)
        return queryset


@method_decorator(user_passes_test(is_admin), name='dispatch')
class CuentaCreateView(LoginRequiredMixin, generic.CreateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = 'catalogo_cuentas/cuenta_form.html'
    success_url = reverse_lazy('cuenta_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nueva Cuenta'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class CuentaUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = 'catalogo_cuentas/cuenta_form.html'
    success_url = reverse_lazy('cuenta_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Cuenta'
        return context

# Vista para Plan de Cuentas Jerárquico
class PlanCuentasView(LoginRequiredMixin, TemplateView):
    template_name = 'catalogo_cuentas/plan_cuentas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtén todas las cuentas principales
        cuentas = Cuenta.objects.filter(parent__isnull=True).prefetch_related('subcuentas')

        def obtener_subcuentas(cuenta):
            return cuenta.subcuentas.all()

        # Prepara cuentas con subcuentas
        cuentas_con_subcuentas = []
        for cuenta in cuentas:
            cuentas_con_subcuentas.append({
                'cuenta': cuenta,
                'subcuentas': obtener_subcuentas(cuenta),
                'has_subcuentas': obtener_subcuentas(cuenta).exists()
            })

        # Agrega paginación y mantiene el nombre `cuentas_con_subcuentas`
        paginator = Paginator(cuentas_con_subcuentas, 2)  # Ajustar número deseado de cuentas por página
        page_number = self.request.GET.get('page')
        cuentas_con_subcuentas = paginator.get_page(page_number)

        context['cuentas_con_subcuentas'] = cuentas_con_subcuentas  # Usa el mismo nombre en el contexto
        return context

        #context['cuentas_con_subcuentas'] = cuentas_con_subcuentas