# comite_pro/bancos/views.py

from django.views import View, generic
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q  # Para buscar registros existentes
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.db.models import Q

from bancos.models import DocumentoBanco
from .forms import DocumentoBancoForm, MovimientoFormSet  
from catalogo_cuentas.models import Cuenta
from transacciones.forms import TransaccionForm

class RegistroDocumentoBancoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        documento_form = DocumentoBancoForm()
        transaccion_form = TransaccionForm()
        movimiento_formset = MovimientoFormSet()
        cuentas = Cuenta.objects.all()  # Obtén las cuentas disponibles
        
        return render(request, 'bancos/documentobanco_form.html', {
            'documento_form': documento_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,  # Pasa las cuentas al contexto
        })

    def post(self, request, *args, **kwargs):
        documento_form = DocumentoBancoForm(request.POST)
        transaccion_form = TransaccionForm(request.POST)
        movimiento_formset = MovimientoFormSet(request.POST)
        cuentas = Cuenta.objects.all()

        # Validar los formularios
        if documento_form.is_valid() and transaccion_form.is_valid() and movimiento_formset.is_valid():
            # Validar que el Debe y el Haber estén correctamente llenos antes de guardar
            movimientos = movimiento_formset.save(commit=False)
            for movimiento in movimientos:
                if (movimiento.debe and movimiento.haber) or (not movimiento.debe and not movimiento.haber):
                    return render(request, 'bancos/documentobanco_form.html', {
                        'documento_form': documento_form,
                        'transaccion_form': transaccion_form,
                        'movimiento_formset': movimiento_formset,
                        'cuentas': cuentas,
                    })

            # Guardar documento bancario
            documento_banco = documento_form.save()
            
            # Guardar transacción
            transaccion = transaccion_form.save(commit=False)
            transaccion.empresa = documento_form.cleaned_data['empresa']
            transaccion.banco = documento_banco

            # Validar que el periodo contable esté abierto
            if not transaccion.periodo:
                messages.error(request, 'Debe seleccionar un periodo para la transacción.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                })
            elif transaccion.periodo.estado != 'Abierto':
                messages.error(request, 'El periodo contable está cerrado. No puede realizar operaciones.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                })
            
            transaccion.save()

            # Verificación de asignación del documento bancario
            if transaccion.banco == documento_banco:
                messages.info(request, 'El documento bancario se ha asociado correctamente con la transacción.')
            else:
                messages.error(request, 'Error al asociar el documento bancario con la transacción.')


            # Guardar movimientos (incluyendo la cuenta asociada a cada movimiento)
            movimiento_formset.instance = transaccion
            movimientos = movimiento_formset.save()

            # Validar que la transacción esté balanceada
            total_debe = sum([mov.debe for mov in movimientos if mov.debe])
            total_haber = sum([mov.haber for mov in movimientos if mov.haber])

            if total_debe != total_haber:
                transaccion.delete()
                documento_banco.delete()
                messages.error(request, 'La transacción no está balanceada. El total del Debe debe ser igual al total del Haber.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                })
            
            messages.success(request, 'El documento bancario y la transacción han sido registrados correctamente.')
            return redirect('documentobanco_list')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            return render(request, 'bancos/documentobanco_form.html', {
                'documento_form': documento_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas' : cuentas,
            })


class DocumentoBancoListView(LoginRequiredMixin, generic.ListView):
    model = DocumentoBanco
    template_name = 'bancos/documentobanco_list.html'
    context_object_name = 'documentos_banco'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Documentos Bancarios'
        return context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Documentos Bancarios'
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(numero_documento__icontains=query) |
                Q(tipo_documento__nombre__icontains=query) |
                Q(empresa__razon_social__icontains=query)
            )
        return queryset
    
class EditarDocumentoBancoView(LoginRequiredMixin, UpdateView):
    model = DocumentoBanco
    form_class = DocumentoBancoForm
    template_name = 'bancos/documentobanco_form.html'
    context_object_name = 'documento_banco'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Documento Bancario'
        return context

    def form_valid(self, form):
        # Verifica que el número de documento no esté repetido.
        if DocumentoBanco.objects.filter(numero_documento=form.cleaned_data['numero_documento']).exclude(pk=self.object.pk).exists():
            form.add_error('numero_documento', 'Este número de documento ya existe.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'El documento bancario ha sido actualizado correctamente.')
        return reverse_lazy('documentobanco_list')