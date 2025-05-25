# comite_pro/transacciones/views.py

from django.views import View, generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q

from django.core.exceptions import ValidationError
from django.db import transaction 
from .forms import MovimientoFormSet, PolizaForm
from catalogo_cuentas.models import Cuenta
from .models import Transaccion, Movimiento

class RegistrarPolizaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        poliza_form = PolizaForm(initial={'tipo_operacion': 'Póliza'})
        movimiento_formset = MovimientoFormSet()
        cuentas = Cuenta.objects.all()  # Todas las cuentas disponibles
        
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
        cuentas = Cuenta.objects.all()  # Todas las cuentas disponibles

        # Validar los formularios
        if poliza_form.is_valid() and movimiento_formset.is_valid():
            # Validar que los movimientos tengan valores correctos de Debe y Haber
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        messages.error(request, 'Debe ingresar un valor en Debe o en Haber, pero no en ambos ni dejar ambos vacíos.')
                        return render(request, 'transacciones/registro_poliza.html', {
                            'poliza_form': poliza_form,
                            'movimiento_formset': movimiento_formset,
                            'cuentas': cuentas,
                            'is_edit': False,
                            'titulo': 'Registrar Póliza',
                        })
        
            # Validar que el periodo contable esté abierto
            periodo = poliza_form.cleaned_data.get('periodo')
            if not periodo:
                messages.error(request, 'Debe seleccionar un periodo contable.')
                return render(request, 'transacciones/registro_poliza.html', {
                    'poliza_form': poliza_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': False,
                    'titulo': 'Registrar Póliza',
                })
            elif periodo.estado != 'Abierto':
                messages.error(request, 'El periodo contable está cerrado. No puede realizar operaciones.')
                return render(request, 'transacciones/registro_poliza.html', {
                    'poliza_form': poliza_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': False,
                    'titulo': 'Registrar Póliza',
                })
            
            try:
                with transaction.atomic():
                    # Crear la transacción (póliza)
                    poliza = poliza_form.save(commit=False)
                    poliza.tipo_operacion = 'Póliza'  # Asegurar que siempre sea tipo Póliza
                    poliza.save()
                    
                    # Procesar los movimientos manualmente
                    movimiento_formset.instance = poliza
                    
                    # Formatear y guardar cada movimiento manualmente
                    movimientos = []
                    for form in movimiento_formset:
                        if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                            movimiento = form.save(commit=False)
                            
                            # Formatear explícitamente con 2 decimales y guardar 0.00 en lugar de NULL
                            debe_valor = form.cleaned_data.get('debe', 0) or 0
                            haber_valor = form.cleaned_data.get('haber', 0) or 0

                            # Siempre guardar valores como números, nunca como NULL
                            movimiento.debe = round(float(debe_valor), 2)
                            movimiento.haber = round(float(haber_valor), 2)
                                
                            movimiento.transaccion = poliza
                            movimiento.save()
                            movimientos.append(movimiento)
                    
                    # Validar que la póliza esté balanceada
                    # Recargamos los movimientos desde la base de datos para cálculos precisos
                    movimientos_activos = Movimiento.objects.filter(transaccion=poliza)
                    
                    # Calcular los totales de los movimientos activos
                    total_debe = sum([mov.debe or 0 for mov in movimientos_activos])
                    total_haber = sum([mov.haber or 0 for mov in movimientos_activos])

                    # Para depuración
                    print(f"Balance: Debe={total_debe}, Haber={total_haber}, Diff={total_debe - total_haber}")
                    
                    if abs(total_debe - total_haber) > 0.01:  # Usar tolerancia de 0.01
                        raise ValidationError('La póliza no está balanceada. El total del Debe debe ser igual al total del Haber.')
                    
                    # Actualizar el monto total de la póliza
                    poliza.monto_total = round(total_debe, 2)  # Asegurar formato decimal
                    poliza.save()

                messages.success(request, 'La póliza ha sido registrada correctamente.')
                return redirect('poliza_list')
            
            except Exception as e:
                # Capturar errores detallados para depuración
                print(f"Error al guardar: {str(e)}")
                
                messages.error(request, f'Error al guardar: {str(e)}')
                return render(request, 'transacciones/registro_poliza.html', {
                    'poliza_form': poliza_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': False,
                    'titulo': 'Registrar Póliza',
                })
        else:
            # Mostrar errores específicos en consola para depuración
            if not poliza_form.is_valid():
                print("Errores en PolizaForm:", poliza_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)
                
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            return render(request, 'transacciones/registro_poliza.html', {
                'poliza_form': poliza_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
                'is_edit': False,
                'titulo': 'Registrar Póliza',
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
        # Obtener la póliza existente
        poliza = get_object_or_404(Transaccion, pk=pk, tipo_operacion='Póliza')
        
        # Preparar datos iniciales para formularios
        initial_data = {
            'fecha': poliza.fecha.strftime('%Y-%m-%d') if poliza.fecha else None
        }

        # Inicializar formularios con instancias existentes
        poliza_form = PolizaForm(instance=poliza, initial=initial_data)
        movimiento_formset = MovimientoFormSet(instance=poliza)

        # Obtener lista de cuentas disponibles (todas las cuentas)
        cuentas = Cuenta.objects.all()

        # Calcular totales para mostrarlos inicialmente
        movimientos = Movimiento.objects.filter(transaccion=poliza)
        total_debe = sum(mov.debe or 0 for mov in movimientos)
        total_haber = sum(mov.haber or 0 for mov in movimientos)

        return render(request, 'transacciones/registro_poliza.html', {
            'poliza_form': poliza_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': True,
            'titulo': 'Editar Póliza',
            'total_debe': total_debe,
            'total_haber': total_haber,
        })
    
    def post(self, request, pk, *args, **kwargs):
        # Obtener la póliza existente
        poliza = get_object_or_404(Transaccion, pk=pk, tipo_operacion='Póliza')
        
        # Inicializar formularios con datos del POST e instancias existentes
        poliza_form = PolizaForm(request.POST, instance=poliza)
        movimiento_formset = MovimientoFormSet(request.POST, instance=poliza)
        cuentas = Cuenta.objects.all()

        # Validar formularios
        if poliza_form.is_valid() and movimiento_formset.is_valid():
            # Validaciones adicionales antes de la transacción
            # Verificar debe/haber
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        messages.error(request, 'Debe ingresar un valor en Debe o en Haber, pero no en ambos ni dejar ambos vacíos.')
                        return render(request, 'transacciones/registro_poliza.html', {
                            'poliza_form': poliza_form,
                            'movimiento_formset': movimiento_formset,
                            'cuentas': cuentas,
                            'is_edit': True,
                            'titulo': 'Editar Póliza',
                        })
                    
            # Verificar periodo contable
            periodo = poliza_form.cleaned_data.get('periodo')
            if not periodo:
                messages.error(request, 'Debe seleccionar un periodo para la póliza.')
                return render(request, 'transacciones/registro_poliza.html', {
                    'poliza_form': poliza_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': True,
                    'titulo': 'Editar Póliza',
                })
            elif periodo.estado != 'Abierto':
                messages.error(request, 'El periodo contable está cerrado. No puede realizar operaciones.')
                return render(request, 'transacciones/registro_poliza.html', {
                    'poliza_form': poliza_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': True,
                    'titulo': 'Editar Póliza',
                })
            
            try:
                with transaction.atomic():
                    # Guardar poliza
                    poliza = poliza_form.save(commit=False)
                    
                    # Asegurar que siempre sea tipo Póliza
                    poliza.tipo_operacion = 'Póliza'
                    poliza.save()
                    
                    # Procesar los movimientos manualmente
                    movimiento_formset.instance = poliza

                    # Primero, manejo de eliminaciones
                    for form in movimiento_formset:
                        if form.is_valid() and form.cleaned_data.get('DELETE', False):
                            if form.instance.pk:
                                form.instance.delete()
                    
                    # Luego, actualizar/crear movimientos
                    for form in movimiento_formset:
                        if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                            movimiento = form.save(commit=False)

                            # Siempre guardar valores como 0.00, nunca como NULL
                            debe_valor = form.cleaned_data.get('debe', 0) or 0
                            haber_valor = form.cleaned_data.get('haber', 0) or 0
                            
                            movimiento.debe = round(float(debe_valor), 2)
                            movimiento.haber = round(float(haber_valor), 2)
                                
                            movimiento.transaccion = poliza
                            movimiento.save()
                    
                    # Volver a cargar los movimientos desde la base de datos para cálculos precisos
                    movimientos_activos = Movimiento.objects.filter(transaccion=poliza)

                    # Calcular los totales de los movimientos activos
                    total_debe = sum(mov.debe or 0 for mov in movimientos_activos)
                    total_haber = sum(mov.haber or 0 for mov in movimientos_activos)

                    # Para depuración
                    print(f"Balance: Debe={total_debe}, Haber={total_haber}, Diff={total_debe - total_haber}")
                    
                    if abs(total_debe - total_haber) > 0.01:  # Usar tolerancia de 0.01
                        raise ValidationError('La póliza no está balanceada. El total del Debe debe ser igual al total del Haber.')
                    
                    # Actualizar monto total de la póliza
                    poliza.monto_total = round(total_debe, 2)  # Asegurar formato decimal
                    poliza.save()
                
                messages.success(request, 'La póliza ha sido actualizada correctamente.')
                return redirect('poliza_list')
            
            except Exception as e:
                # Mostrar errores específicos en consola para depuración
                print(f"Error al guardar: {str(e)}")
                
                messages.error(request, f'Error al guardar: {str(e)}')
                return render(request, 'transacciones/registro_poliza.html', {
                    'poliza_form': poliza_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': True,
                    'titulo': 'Editar Póliza',
                })
                
        else:
            # Mostrar errores específicos en consola para depuración
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
                'total_debe': sum(form.cleaned_data.get('debe', 0) or 0 for form in movimiento_formset if form.is_valid() and not form.cleaned_data.get('DELETE', False)),
                'total_haber': sum(form.cleaned_data.get('haber', 0) or 0 for form in movimiento_formset if form.is_valid() and not form.cleaned_data.get('DELETE', False)),
            })

    
