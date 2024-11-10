# comite_pro/transacciones/views.py

from django.views import View, generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.db import transaction 


from .forms import TransaccionForm, MovimientoFormSet, PolizaForm
from documentos.forms import DocComprobanteForm
from catalogo_cuentas.models import Cuenta
from .models import Transaccion
from django.views.generic import UpdateView
from django.urls import reverse_lazy

class RegistrarComprobanteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        doc_form = DocComprobanteForm()
        transaccion_form = TransaccionForm()
        movimiento_formset = MovimientoFormSet()
        cuentas = Cuenta.objects.all() # Obtén las cuentas disponibles

        return render(request, 'transacciones/registrar_comprobante.html', {
            'doc_form': doc_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas, # Pasa las cuentas al contexto
        })

    def post(self, request, *args, **kwargs):
        doc_form = DocComprobanteForm(request.POST)
        transaccion_form = TransaccionForm(request.POST)
        movimiento_formset = MovimientoFormSet(request.POST)
        cuentas = Cuenta.objects.all()
            
        # Validar los formularios
        if doc_form.is_valid() and transaccion_form.is_valid() and movimiento_formset.is_valid():
            # Validar que el Debe y el Haber estén correctamente llenos antes de guardar
            movimientos = movimiento_formset.save(commit=False)
            for movimiento in movimientos:
                if (movimiento.debe and movimiento.haber) or (not movimiento.debe and not movimiento.haber):
                    return render(request, 'transacciones/registrar_comprobante.html', {
                    'doc_form': doc_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas, 
                    })

            # Guardar DocComprobante
            doc_comprobante = doc_form.save()

            # Guardar Transaccion
            transaccion = transaccion_form.save(commit=False)
            transaccion.empresa = doc_form.cleaned_data['empresa']
            transaccion.comprobante = doc_comprobante
            
            # Validar que el periodo contable esté abierto
            if not transaccion.periodo:
                messages.error(request, 'Debe seleccionar un periodo para la transacción.')
                return render(request, 'transacciones/registrar_comprobante.html', {
                'doc_form': doc_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas, 
                })
            elif transaccion.periodo.estado != 'Abierto':
                messages.error(request, 'El periodo contable está cerrado. No puede realizar operaciones.')
                return render(request, 'transacciones/registrar_comprobante.html', {
                'doc_form': doc_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas, 
                })
            
            transaccion.save()

            # Guardar Movimientos (incluyendo la cuenta asociada a cada movimiento)
            movimiento_formset.instance = transaccion
            movimientos = movimiento_formset.save()

            # Validar que la transacción esté balanceada 
            total_debe = sum([mov.debe for mov in movimientos if mov.debe])
            total_haber = sum([mov.haber for mov in movimientos if mov.haber])
            
            if total_debe != total_haber:
                # Eliminar transacción y comprobante si no está balanceada
                transaccion.delete()  
                doc_comprobante.delete()
                messages.error(request, 'La transacción no está balanceada. El total del Debe debe ser igual al total del Haber.')
                return render(request, 'transacciones/registrar_comprobante.html', {
                    'doc_form': doc_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                })
            
            messages.success(request, 'El comprobante y la transacción han sido registrados correctamente.')
            return redirect('doccomprobante_list')
        
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            return render(request, 'transacciones/registrar_comprobante.html', {
                'doc_form': doc_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
            })

class RegistrarPolizaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        poliza_form = PolizaForm(initial={'tipo_operacion': 'Póliza'})
        movimiento_formset = MovimientoFormSet()
        cuentas = Cuenta.objects.all()
        return render(request, 'transacciones/registro_poliza.html', {
            'poliza_form': poliza_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': False,
            'titulo': 'Registrar Póliza',
        })

    def post(self, request, *args, **kwargs):
        poliza_form = PolizaForm(request.POST)
        movimiento_formset = MovimientoFormSet(request.POST)
        cuentas = Cuenta.objects.all()

        if poliza_form.is_valid() and movimiento_formset.is_valid():
            with transaction.atomic():
                # Crear la transacción (póliza)
                poliza = poliza_form.save(commit=False)
                poliza.tipo_operacion = 'Póliza'
                poliza.save()

                # Asignar la póliza al formset y guardar los movimientos
                movimiento_formset.instance = poliza
                movimiento_formset.save()

                messages.success(request, 'La póliza ha sido registrada correctamente.')
                return redirect('poliza_list')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            return render(request, 'transacciones/registro_poliza.html', {
                'poliza_form': poliza_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
            })
        

class PolizaListView(LoginRequiredMixin, generic.ListView):
    model = Transaccion
    template_name = 'transacciones/poliza_list.html'
    context_object_name = 'polizas'
    paginate_by = 10  # Puedes ajustar este valor según tus necesidades

    def get_queryset(self):
        # Obtener el término de búsqueda desde la consulta GET
        query = self.request.GET.get('query', '')
        queryset = Transaccion.objects.filter(tipo_operacion='Póliza').order_by('-fecha')

        # Filtrar las transacciones para obtener solo las pólizas que coincidan con el término de búsqueda
        if query:
            queryset = queryset.filter(
                Q(numero_poliza__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(empresa__razon_social__icontains=query)
            )
        return queryset

class ActualizarPolizaView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        poliza = get_object_or_404(Transaccion, pk=pk, tipo_operacion='Póliza')
        poliza_form = PolizaForm(instance=poliza)
        movimiento_formset = MovimientoFormSet(instance=poliza)
        cuentas = Cuenta.objects.all()
        return render(request, 'transacciones/registro_poliza.html', {
            'poliza_form': poliza_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': True,  # Indicador de modo edición
            'titulo': 'Editar Póliza',
        })

    def post(self, request, pk, *args, **kwargs):
        poliza = get_object_or_404(Transaccion, pk=pk, tipo_operacion='Póliza')
        poliza_form = PolizaForm(request.POST, instance=poliza)
        movimiento_formset = MovimientoFormSet(request.POST, instance=poliza)
        cuentas = Cuenta.objects.all()

        print(f"Fecha (antes de la validación): {request.POST.get('fecha')}")
        print(f"POST data: {request.POST}")

        if poliza_form.is_valid() and movimiento_formset.is_valid():
            with transaction.atomic():
                # Guardar la póliza sin monto_total por ahora
                poliza = poliza_form.save(commit=False)
                poliza.tipo_operacion = 'Póliza'
                poliza.save()

                # Guardar los movimientos
                movimiento_formset.instance = poliza
                movimiento_formset.save()

                messages.success(request, 'La póliza ha sido actualizada correctamente.')
                return redirect('poliza_list')
        else:
            # Mostrar errores específicos en consola
            if not poliza_form.is_valid():
                print("Errores en PolizaForm:", poliza_form.errors)

            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)

            messages.error(request, 'Por favor, corrige los errores en el formulario.')

        return render(request, 'transacciones/registro_poliza.html', {
            'poliza_form': poliza_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': True,
            'titulo': 'Editar Póliza',
        })
        

    
