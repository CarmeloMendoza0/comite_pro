#comite_pro/empresa/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views import generic
from .models import Empresa, PeriodoContable
from .forms import EmpresaForm, PeriodoContableForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from comite_pro.utils import is_admin, is_accountant 

@method_decorator(user_passes_test(is_admin), name='dispatch')
class EmpresaFormView(LoginRequiredMixin, generic.CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "empresa/empresa_form.html"
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Agregar usuarios a la empresa
        form.instance.usuario.set(form.cleaned_data['usuarios'])
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nueva Empresa'
        return context
    
@method_decorator(user_passes_test(is_admin), name='dispatch')
class EmpresaUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresa/empresa_form.html'
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Actualizar usuarios asignados a la empresa
        form.instance.usuario.set(form.cleaned_data['usuarios'])
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Empresa'
        return context
    
class EmpresasListView(LoginRequiredMixin, generic.ListView):
    model = Empresa
    template_name = 'empresa/empresa_list.html' 
    context_object_name = 'empresas'  
    paginate_by = 10  

    def get_queryset(self):
        return Empresa.objects.all()  
    
    def get_queryset(self):
        return Empresa.objects.filter(usuario=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Empresas'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class PeriodoContableCreateView(LoginRequiredMixin, generic.CreateView):
    model = PeriodoContable
    form_class = PeriodoContableForm
    template_name = "empresa/periodos_form.html"
    success_url = reverse_lazy('lista_periodos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Periodo Contable'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class PeriodoContableListView(LoginRequiredMixin, generic.ListView):
    model = PeriodoContable
    template_name = "empresa/periodos_list.html"
    context_object_name = 'periodos'
    paginate_by = 10
    ordering = ['fecha_inicio']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Periodos Contables'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class CambiarEstadoPeriodoView(LoginRequiredMixin, generic.View):
    def post(self, request, pk, *args, **kwargs):
        periodo = get_object_or_404(PeriodoContable, pk=pk)
        # Cambiar el estado
        if periodo.estado == 'Cerrado':
            periodo.estado = 'Abierto'
        else:
            periodo.estado = 'Cerrado'
        periodo.save()
        return HttpResponseRedirect(reverse('lista_periodos'))