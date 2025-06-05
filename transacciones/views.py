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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json

@login_required
@csrf_exempt
def verificar_credencial_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            clave_ingresada = data.get('clave', '')
            
            # Verificar contra la clave configurada en settings
            clave_correcta = getattr(settings, 'ADMIN_VERIFICATION_KEY', 'ADM1N_S3CUR3')
            
            return JsonResponse({
                'valida': clave_ingresada == clave_correcta
            })
        except:
            return JsonResponse({'valida': False})
    
    return JsonResponse({'valida': False})

class RegistrarPolizaView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        poliza_form = PolizaForm(initial={'tipo_operacion': 'Póliza'}, is_edit=False)  # Pasar is_edit=False
        movimiento_formset = MovimientoFormSet()
        #Filtrar solo cuentas activas
        cuentas = Cuenta.objects.filter(activo=True, nivel__in=[2, 3]).order_by('nivel', 'codigo')
        
        return render(request, 'transacciones/registro_poliza.html', {
            'poliza_form': poliza_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': False,
            'titulo': 'Registrar Póliza',
        })

    def post(self, request, *args, **kwargs):
        poliza_form = PolizaForm(request.POST, is_edit=False)  # Pasar is_edit=False
        movimiento_formset = MovimientoFormSet(request.POST)
        # Filtrar solo cuentas activas
        cuentas = Cuenta.objects.filter(activo=True, nivel__in=[2, 3]).order_by('nivel', 'codigo')

        # Definir función helper para renderizar en caso de error
        def render_error_response(error_message=None):
            if error_message:
                messages.error(request, error_message)
            
            # Calcular totales para mostrar en caso de error
            total_debe = 0
            total_haber = 0
            
            # CRITICAL FIX: Normalizar valores para que el template los muestre correctamente
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    total_debe += float(debe)
                    total_haber += float(haber)
                
                # NORMALIZACIÓN: Preservar todos los valores del formulario correctamente
                if hasattr(form, 'data') and form.data:
                    # Preservar cuenta seleccionada
                    cuenta_field = f"{form.prefix}-cuenta"
                    if cuenta_field in form.data:
                        # Asegurar que la cuenta se preserve en initial
                        form.initial = form.initial or {}
                        form.initial['cuenta'] = form.data[cuenta_field]
                    
                    # Preservar y normalizar valores numéricos
                    debe_field = f"{form.prefix}-debe"
                    haber_field = f"{form.prefix}-haber"
                    
                    if debe_field in form.data:
                        try:
                            debe_normalized = f"{float(str(form.data[debe_field]).replace(',', '.')):.2f}"
                            form.initial['debe'] = debe_normalized
                        except (ValueError, TypeError):
                            form.initial['debe'] = "0.00"
                    
                    if haber_field in form.data:
                        try:
                            haber_normalized = f"{float(str(form.data[haber_field]).replace(',', '.')):.2f}"
                            form.initial['haber'] = haber_normalized
                        except (ValueError, TypeError):
                            form.initial['haber'] = "0.00"
            
            # Calcular diferencia (ajuste contable)
            balance_diff = round(total_debe - total_haber, 2)
            
            return render(request, 'transacciones/registro_poliza.html', {
                'poliza_form': poliza_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
                'is_edit': False,
                'titulo': 'Registrar Póliza',
                'total_debe': total_debe,
                'total_haber': total_haber,
                'balance_diff': balance_diff,
                'preserve_formset_data': True,  # Flag para JavaScript
            })

        # Validar los formularios
        if poliza_form.is_valid() and movimiento_formset.is_valid():
            # Validar que los movimientos tengan valores correctos de Debe y Haber
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        return render_error_response('Debe ingresar un valor en Debe o en Haber, pero no en ambos ni dejar ambos vacíos.')
        
            # Validar que el periodo contable esté abierto
            periodo = poliza_form.cleaned_data.get('periodo')
            if not periodo:
                return render_error_response('Debe seleccionar un periodo contable.')
            elif periodo.estado != 'Abierto':
                return render_error_response('El periodo contable está cerrado. No puede realizar operaciones.')
            
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
                return render_error_response(f'Error al guardar: {str(e)}')
        else:
            # Mostrar errores específicos en consola para depuración
            if not poliza_form.is_valid():
                print("Errores en PolizaForm:", poliza_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)
                
            return render_error_response('Por favor, corrige los errores en el formulario.')

class PolizaListView(LoginRequiredMixin, generic.ListView):
    model = Transaccion
    template_name = 'transacciones/poliza_list.html'
    context_object_name = 'polizas'
    paginate_by = 10 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar información sobre filtros activos
        context['mostrar_inactivos'] = self.request.GET.get('mostrar_inactivos') == 'true'
        return context

    # Obtener el término de búsqueda desde la consulta GET query = self.request.GET.get('query', '') queryset = Transaccion.objects.filter(tipo_operacion='Póliza').order_by('-fecha')
    def get_queryset(self):
        query = self.request.GET.get('query', '')
        #Por defecto, mostrar solo pólizas activas
        if self.request.GET.get('mostrar_inactivos') == 'true':
            queryset = Transaccion.objects.filter(tipo_operacion='Póliza')
        else:
            queryset = Transaccion.activos()
        # Filtrar las transacciones para obtener solo las pólizas que coincidan con el término de búsqueda
        queryset = queryset.order_by('-fecha')
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
        poliza_form = PolizaForm(instance=poliza, initial=initial_data, is_edit=True)  # Pasar is_edit=True
        movimiento_formset = MovimientoFormSet(instance=poliza)

        # Filtrar solo cuentas activas        cuentas = Cuenta.objects.all()
        cuentas = Cuenta.objects.filter(activo=True)

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
        poliza_form = PolizaForm(request.POST, instance=poliza, is_edit=True)  # Pasar is_edit=True
        movimiento_formset = MovimientoFormSet(request.POST, instance=poliza)
        # CAMBIO: Filtrar solo cuentas activas cuentas = Cuenta.objects.all()
        cuentas = Cuenta.objects.filter(activo=True)
        

        # Función helper para renderizar en caso de error
        def render_error_response(error_message=None):
            if error_message:
                messages.error(request, error_message)
            
            # Calcular totales para mostrar en caso de error
            total_debe = 0
            total_haber = 0
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    total_debe += float(debe)
                    total_haber += float(haber)
                    
            # Calcular diferencia (ajuste contable)
            balance_diff = round(total_debe - total_haber, 2)
                    
            return render(request, 'transacciones/registro_poliza.html', {
                'poliza_form': poliza_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
                'is_edit': True,
                'titulo': 'Editar Póliza',
                'total_debe': total_debe,
                'total_haber': total_haber,
                'balance_diff': balance_diff,
                'preserve_formset_data': True,  # Flag para JavaScript
            })

        # Validar formularios
        if poliza_form.is_valid() and movimiento_formset.is_valid():
            # Validaciones adicionales antes de la transacción
            # Verificar debe/haber
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        return render_error_response('Debe ingresar un valor en Debe o en Haber, pero no en ambos ni dejar ambos vacíos.')
                    
            # Verificar periodo contable
            periodo = poliza_form.cleaned_data.get('periodo')
            if not periodo:
                return render_error_response('Debe seleccionar un periodo para la póliza.')
            elif periodo.estado != 'Abierto':
                return render_error_response('El periodo contable está cerrado. No puede realizar operaciones.')
            
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
                return render_error_response(f'Error al guardar: {str(e)}')
                
        else:
            # Mostrar errores específicos en consola para depuración
            if not poliza_form.is_valid():
                print("Errores en PolizaForm:", poliza_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)
            
            return render_error_response('Por favor, corrige los errores en el formulario.')

class EliminarPolizaView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        poliza = get_object_or_404(Transaccion, pk=pk, tipo_operacion='Póliza')
        
        # Verificar que la póliza esté activa
        if not poliza.activo:
            messages.warning(request, 'La póliza ya está desactivada.')
            return redirect('poliza_list')
        
        # Desactivar la póliza en lugar de eliminarla
        poliza.desactivar()
        
        messages.success(request, f'La póliza {poliza.numero_poliza} ha sido desactivada correctamente.')
        return redirect('poliza_list')
    

