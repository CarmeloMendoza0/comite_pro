# comite_pro/documentos/views.py

from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import TipoDocumento, DocComprobante
from .forms import TipoDocumentoForm, DocComprobanteForm

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from comite_pro.utils import is_admin, is_accountant  # Importa las funciones
from django.db.models import Q  # Importar Q para consultas complejas


# Vistas para TipoDocumento

class TipoDocumentoListView(LoginRequiredMixin, generic.ListView):
    model = TipoDocumento
    template_name = 'documentos/tipodocumento_list.html'
    context_object_name = 'tipos_documento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Tipos de Documento'
        return context
    
@method_decorator(user_passes_test(is_admin), name='dispatch')
class TipoDocumentoCreateView(LoginRequiredMixin, generic.CreateView):
    model = TipoDocumento
    form_class = TipoDocumentoForm
    template_name = 'documentos/tipodocumento_form.html'
    success_url = reverse_lazy('tipodocumento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Tipo de Documento'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class TipoDocumentoUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TipoDocumento
    form_class = TipoDocumentoForm
    template_name = 'documentos/tipodocumento_form.html'
    success_url = reverse_lazy('tipodocumento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Tipo de Documento'
        return context

# Vistas para DocComprobante

class DocComprobanteListView(LoginRequiredMixin, generic.ListView):
    model = DocComprobante
    template_name = 'documentos/doccomprobante_list.html'
    context_object_name = 'documentos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Comprobantes'
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')

        if query:
            queryset = queryset.filter(
                Q(numero_documento__icontains=query) |
                Q(empresa__razon_social__icontains=query) |
                Q(tipo_documento__nombre__icontains=query)
            ).distinct()
        return queryset

class DocComprobanteCreateView(LoginRequiredMixin, generic.CreateView):
    model = DocComprobante
    form_class = DocComprobanteForm
    template_name = 'documentos/doccomprobante_form.html'
    success_url = reverse_lazy('doccomprobante_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Comprobante'
        return context

class DocComprobanteUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = DocComprobante
    form_class = DocComprobanteForm
    template_name = 'documentos/doccomprobante_form.html'
    success_url = reverse_lazy('doccomprobante_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Comprobante'
        return context
