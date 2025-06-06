#comite_pro/terceros/views.py
# Create your views here.

from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from comite_pro.utils import is_admin, is_accountant 
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib import messages
from .models import Proveedor, Persona
from .forms import ProveedorForm, ClienteForm, DonanteForm

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin

# Cliente Views
@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class ClienteCreateView(generic.CreateView):
    model = Persona
    form_class = ClienteForm
    template_name = 'terceros/form_base.html'
    success_url = reverse_lazy('cliente_list')

    def get_initial(self):
        initial = super().get_initial()
        initial['tipo'] = Persona.CLIENTE
        return initial

    def form_valid(self, form):
        form.instance.tipo = Persona.CLIENTE
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Cliente'
        context['url_list'] = reverse_lazy('cliente_list')
        return context

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class ClienteUpdateView(generic.UpdateView):
    model = Persona
    form_class = ClienteForm
    template_name = 'terceros/form_base.html'
    success_url = reverse_lazy('cliente_list')

    def get_queryset(self):
        return Persona.objects.filter(tipo=Persona.CLIENTE, empresa__usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Cliente'
        context['url_list'] = reverse_lazy('cliente_list')
        return context

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class ClienteListView(generic.ListView):
    model = Persona
    template_name = 'terceros/list_base.html'
    context_object_name = 'items'
    paginate_by = 10

    def get_queryset(self):
        queryset = Persona.objects.filter(
            tipo=Persona.CLIENTE,
            activo=True,
            empresa__usuario=self.request.user
        )

        # Búsqueda
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                nombre__icontains=query
            ).distinct()
        
        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Clientes'
        context['url_create'] = reverse_lazy('cliente_create')
        context['url_edit'] = 'cliente_update'
        context['item_type'] = 'Cliente'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class ClienteDeleteView(LoginRequiredMixin, generic.View):
    """Vista para desactivar cliente (eliminación lógica)"""
    
    def post(self, request, pk):
        try:
            cliente = Persona.objects.get(pk=pk, tipo=Persona.CLIENTE, empresa__usuario=request.user)
            cliente.desactivar()
            messages.success(request, f'Cliente "{cliente.nombre}" desactivado exitosamente.')
        except Persona.DoesNotExist:
            messages.error(request, 'El cliente no existe.')
        
        return HttpResponseRedirect(reverse_lazy('cliente_list'))


# Donante Views
@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class DonanteCreateView(generic.CreateView):
    model = Persona
    form_class = DonanteForm
    template_name = 'terceros/form_base.html'
    success_url = reverse_lazy('donante_list')

    def get_initial(self):
        initial = super().get_initial()
        initial['tipo'] = Persona.DONANTE
        return initial

    def form_valid(self, form):
        form.instance.tipo = Persona.DONANTE
        messages.success(self.request, 'Donante creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Donante'
        context['url_list'] = reverse_lazy('donante_list')
        return context

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class DonanteUpdateView(generic.UpdateView):
    model = Persona
    form_class = DonanteForm
    template_name = 'terceros/form_base.html'
    success_url = reverse_lazy('donante_list')

    def get_queryset(self):
        return Persona.objects.filter(tipo=Persona.DONANTE, empresa__usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Donante actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Donante'
        context['url_list'] = reverse_lazy('donante_list')
        return context

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class DonanteListView(generic.ListView):
    model = Persona
    template_name = 'terceros/list_base.html'
    context_object_name = 'items'
    paginate_by = 10

    def get_queryset(self):
        queryset = Persona.objects.filter(
            tipo=Persona.DONANTE,
            activo=True,
            empresa__usuario=self.request.user
        )
        
        # Búsqueda
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                nombre__icontains=query
            ).distinct()
        
        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Donantes'
        context['url_create'] = reverse_lazy('donante_create')
        context['url_edit'] = 'donante_update'
        context['item_type'] = 'Donante'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class DonanteDeleteView(LoginRequiredMixin, generic.View):
    """Vista para desactivar donante (eliminación lógica)"""
    
    def post(self, request, pk):
        try:
            donante = Persona.objects.get(pk=pk, tipo=Persona.DONANTE, empresa__usuario=request.user)
            donante.desactivar()
            messages.success(request, f'Donante "{donante.nombre}" desactivado exitosamente.')
        except Persona.DoesNotExist:
            messages.error(request, 'El donante no existe.')
        
        return HttpResponseRedirect(reverse_lazy('donante_list'))

# Proveedor Views
@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class ProveedorCreateView(generic.CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'terceros/form_base.html'
    success_url = reverse_lazy('proveedor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Proveedor creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Proveedor'
        context['url_list'] = reverse_lazy('proveedor_list')
        return context

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class ProveedorUpdateView(generic.UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'terceros/form_base.html'
    success_url = reverse_lazy('proveedor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Proveedor actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Proveedor'
        context['url_list'] = reverse_lazy('proveedor_list')
        return context
    
@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class ProveedorListView(generic.ListView):
    model = Proveedor
    template_name = 'terceros/list_base.html'
    context_object_name = 'items'
    paginate_by = 10

    def get_queryset(self):
        queryset = Proveedor.objects.filter(
            activo=True,
            empresa__usuario=self.request.user
        )
        
        # Búsqueda
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                nombre__icontains=query
            ).distinct()
        
        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Proveedores'
        context['url_create'] = reverse_lazy('proveedor_create')
        context['url_edit'] = 'proveedor_update'
        context['item_type'] = 'Proveedor'
        return context
    
@method_decorator(user_passes_test(is_admin), name='dispatch') 
class ProveedorDeleteView(LoginRequiredMixin, generic.View):
    """Vista para desactivar proveedor (eliminación lógica)"""
    
    def post(self, request, pk):
        try:
            proveedor = Proveedor.objects.get(pk=pk, empresa__usuario=request.user)
            proveedor.desactivar()
            messages.success(request, f'Proveedor "{proveedor.nombre}" desactivado exitosamente.')
        except Proveedor.DoesNotExist:
            messages.error(request, 'El proveedor no existe.')
        
        return HttpResponseRedirect(reverse_lazy('proveedor_list'))    
    
