# comite_pro/bancos/views.py

from django.db import transaction
from django.views import View, generic
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q  # Para buscar registros existentes

from django.core.exceptions import ValidationError
from bancos.models import DocumentoBanco
from catalogo_cuentas.models import Cuenta
from transacciones.models import Movimiento, Transaccion
from .forms import DocumentoBancoForm, MovimientoFormSet  
from transacciones.forms import TransaccionForm

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

class RegistroDocumentoBancoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        documento_form = DocumentoBancoForm(is_edit=False)
        transaccion_form = TransaccionForm(is_edit=False)
        movimiento_formset = MovimientoFormSet()
        cuentas = Cuenta.objects.filter(activo=True, nivel__in=[2, 3]).order_by('nivel', 'codigo')  
        
        return render(request, 'bancos/documentobanco_form.html', {
            'documento_form': documento_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,  # Pasa las cuentas al contexto
            'is_edit': False,
            'titulo': 'Registrar Documento Bancario',
        })

    def post(self, request, *args, **kwargs):
        documento_form = DocumentoBancoForm(request.POST, is_edit=False)
        transaccion_form = TransaccionForm(request.POST, is_edit=False)
        movimiento_formset = MovimientoFormSet(request.POST)
        cuentas = Cuenta.objects.filter(activo=True, nivel__in=[2, 3]).order_by('nivel', 'codigo')

        # Obtener el tipo de movimiento del formulario
        tipo_movimiento = request.POST.get('tipo_movimiento')

        # Definir función helper para renderizar en caso de error con preservación de datos
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
            
            return render(request, 'bancos/documentobanco_form.html', {
                'documento_form': documento_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
                'is_edit': False,
                'titulo': 'Registrar Documento Bancario',
                'tipo_movimiento_previo': tipo_movimiento,  # Pasar el tipo seleccionado
                'total_debe': total_debe,
                'total_haber': total_haber,
                'balance_diff': balance_diff,
                'preserve_formset_data': True,  # Flag para JavaScript
            })

        # Validar los formularios
        if documento_form.is_valid() and transaccion_form.is_valid() and movimiento_formset.is_valid():
            # Validar que el Debe y el Haber estén correctamente llenos antes de guardar
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        return render_error_response('Debe ingresar un valor en Debe o en Haber, pero no en ambos.')
                    
            # Validar que el periodo contable esté abierto
            periodo = transaccion_form.cleaned_data.get('periodo')
            if not periodo:
                return render_error_response('Debe seleccionar un periodo para la transacción.')
            elif periodo.estado != 'Abierto':
                return render_error_response('No puede realizar operaciones.')

            try:
                with transaction.atomic():
                    # Guardar documento bancario
                    documento_banco = documento_form.save()
                    
                    # Guardar transacción
                    transaccion = transaccion_form.save(commit=False)
                    transaccion.empresa = documento_form.cleaned_data['empresa']
                    transaccion.banco = documento_banco

                    # Establecer tipo_transaccion según la selección de la modal
                    if tipo_movimiento == 'ingreso':
                        transaccion.tipo_transaccion = 'Ingreso'
                    elif tipo_movimiento == 'egreso':
                        transaccion.tipo_transaccion = 'Egreso'
                    
                    transaccion.save()

                    # Procesar los movimientos manualmente
                    movimiento_formset.instance = transaccion

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
                                
                            movimiento.transaccion = transaccion
                            movimiento.save()
                            movimientos.append(movimiento)

                    # Validar que la transacción esté balanceada
                    movimientos_activos = Movimiento.objects.filter(transaccion=transaccion)
                            
                    # Calcular los totales de los movimientos activos
                    total_debe = sum([mov.debe or 0 for mov in movimientos_activos])
                    total_haber = sum([mov.haber or 0 for mov in movimientos_activos])

                    # Para depuración
                    print(f"Balance: Debe={total_debe}, Haber={total_haber}, Diff={total_debe - total_haber}")
                    print("Movimientos activos:", movimientos_activos)

                    if abs(total_debe - total_haber) > 0.01:
                        raise ValidationError('La transacción no está balanceada. El total del Debe debe ser igual al total del Haber.')

                    # Obtener valores del formulario
                    documento_monto = documento_form.cleaned_data.get('monto')
                    transaccion_monto = transaccion_form.cleaned_data.get('monto_total')
                    
                    # Solo actualizar si no hay valor en el formulario
                    if not transaccion_monto or transaccion_monto == 0:
                        transaccion.monto_total = round(total_debe, 2)  # Asegurar formato decimal
                        transaccion.save()
                    
                    # Solo actualizar si no hay valor en el formulario
                    if not documento_monto or documento_monto == 0:
                        documento_banco.monto = round(total_debe, 2)  # Asegurar formato decimal
                        documento_banco.save()

                    # Verificación de asignación del documento bancario (después de guardar)
                    if transaccion.banco == documento_banco:
                        messages.info(request, 'El documento bancario se ha asociado correctamente con la transacción.')

                messages.success(request, 'El documento bancario y la transacción han sido registrados correctamente.')
                return redirect('documentobanco_list')
            
            except Exception as e:
                return render_error_response(f'Error al guardar: {str(e)}')
        else:
            # Mostrar errores específicos en consola para depuración
            if not documento_form.is_valid():
                print("Errores en DocumentoBancoForm:", documento_form.errors)
            
            if not transaccion_form.is_valid():
                print("Errores en TransaccionForm:", transaccion_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)

            return render_error_response('Por favor, corrige los errores en el formulario.')

class DocumentoBancoListView(LoginRequiredMixin, generic.ListView):
    model = DocumentoBanco
    template_name = 'bancos/documentobanco_list.html'
    context_object_name = 'documentos_banco'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista de Documentos Bancarios'
        context['mostrar_inactivos'] = self.request.GET.get('mostrar_inactivos') == 'true'
        return context

    def get_queryset(self):
        #queryset = super().get_queryset()
        if self.request.GET.get('mostrar_inactivos') == 'true':
            queryset = DocumentoBanco.objects.all()
        else:
            queryset = DocumentoBanco.activos()

        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(numero_documento__icontains=query) |
                Q(tipo_documento__nombre__icontains=query) |
                Q(empresa__razon_social__icontains=query)
            ).distinct()

        return queryset.order_by('-fecha', 'numero_documento')
    
class EditarDocumentoBancoView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # Obtener el documento bancario existente
        documento_banco = get_object_or_404(DocumentoBanco, pk=pk)
        
        # Buscar la transacción asociada al documento bancario
        transaccion = Transaccion.objects.filter(banco=documento_banco).first()
        
        if not transaccion:
            messages.error(request, 'No se encontró una transacción asociada a este documento bancario.')
            return redirect('documentobanco_list')
        
        # Preparar datos iniciales para formularios
        initial_data = {
            'fecha': documento_banco.fecha.strftime('%Y-%m-%d') if documento_banco.fecha else None
        }

        # Inicializar formularios con instancias existentes
        documento_form = DocumentoBancoForm(instance=documento_banco, initial=initial_data, is_edit=True)
        transaccion_form = TransaccionForm(
            instance=transaccion, 
            initial={'fecha': transaccion.fecha.strftime('%Y-%m-%d') if transaccion.fecha else None}, 
            is_edit=True)
        movimiento_formset = MovimientoFormSet(instance=transaccion)

        # Obtener lista de cuentas ACTIVAS disponibles
        cuentas = Cuenta.objects.filter(activo=True, nivel__in=[2, 3]).order_by('nivel', 'codigo')

        # Calcular totales para mostrarlos inicialmente
        movimientos = Movimiento.objects.filter(transaccion=transaccion)
        total_debe = sum(mov.debe or 0 for mov in movimientos)
        total_haber = sum(mov.haber or 0 for mov in movimientos)

        # Determinar el tipo de movimiento basado en la transacción existente
        tipo_movimiento_actual = None
        if transaccion.tipo_transaccion == 'Ingreso':
            tipo_movimiento_actual = 'ingreso'
        elif transaccion.tipo_transaccion == 'Egreso':
            tipo_movimiento_actual = 'egreso'

        return render(request, 'bancos/documentobanco_form.html', {
            'documento_form': documento_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': True,  # Indicador de modo edición
            'titulo': 'Editar Documento Bancario',
            'total_debe': total_debe,
            'total_haber': total_haber,
            'tipo_movimiento_previo': tipo_movimiento_actual,  # Pasar el tipo actual
        })
    
    def post(self, request, pk, *args, **kwargs):
        # Obtener instancias existentes
        documento_banco = get_object_or_404(DocumentoBanco, pk=pk)
        transaccion = Transaccion.objects.filter(banco=documento_banco).first()
        
        if not transaccion:
            messages.error(request, 'No se encontró una transacción asociada a este documento bancario.')
            return redirect('documentobanco_list')
        
        # Inicializar formularios con datos del POST e instancias existentes
        documento_form = DocumentoBancoForm(request.POST, instance=documento_banco, is_edit=True)
        transaccion_form = TransaccionForm(request.POST, instance=transaccion, is_edit=True)
        movimiento_formset = MovimientoFormSet(request.POST, instance=transaccion)

        cuentas = Cuenta.objects.filter(activo=True, nivel__in=[2, 3]).order_by('nivel', 'codigo')

        # Obtener el tipo de movimiento del formulario
        tipo_movimiento = request.POST.get('tipo_movimiento')   

        # Función helper para renderizar en caso de error con preservación de datos
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
            
            return render(request, 'bancos/documentobanco_form.html', {
                'documento_form': documento_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas': cuentas,
                'is_edit': True,
                'titulo': 'Editar Documento Bancario',
                'tipo_movimiento_previo': tipo_movimiento,  # Preservar el tipo seleccionado
                'total_debe': total_debe,
                'total_haber': total_haber,
                'balance_diff': balance_diff,
                'preserve_formset_data': True,  # Flag para JavaScript
            })

        # Validar formularios
        if documento_form.is_valid() and transaccion_form.is_valid() and movimiento_formset.is_valid():
            # Validaciones adicionales antes de la transacción
            # Verificar debe/haber
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        return render_error_response('Debe ingresar un valor en Debe o en Haber, pero no en ambos.')
                    
            # Verificar periodo contable
            periodo = transaccion_form.cleaned_data.get('periodo')
            if not periodo:
                return render_error_response('Debe seleccionar un periodo para la transacción.')
            elif periodo.estado != 'Abierto':
                return render_error_response('No puede realizar operaciones.')
            
            try:
                with transaction.atomic():
                    # Guardar documento bancario
                    documento_banco = documento_form.save()
                    
                    # Guardar transacción
                    transaccion = transaccion_form.save(commit=False)
                    transaccion.empresa = documento_form.cleaned_data['empresa']
                    transaccion.banco = documento_banco

                    # Establecer tipo_transaccion según la selección de la modal
                    if tipo_movimiento == 'ingreso':
                        transaccion.tipo_transaccion = 'Ingreso'
                    elif tipo_movimiento == 'egreso':
                        transaccion.tipo_transaccion = 'Egreso'

                    transaccion.save()

                    # Procesar los movimientos manualmente
                    movimiento_formset.instance = transaccion

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

                            movimiento.transaccion = transaccion
                            movimiento.save()

                    # Volver a cargar los movimientos desde la base de datos para cálculos precisos
                    movimientos_activos = Movimiento.objects.filter(transaccion=transaccion)

                    # Calcular los totales de los movimientos activos
                    total_debe = sum(mov.debe or 0 for mov in movimientos_activos)
                    total_haber = sum(mov.haber or 0 for mov in movimientos_activos)

                    # Para depuración
                    print(f"Balance: Debe={total_debe}, Haber={total_haber}, Diff={total_debe - total_haber}")
                    print("Movimientos activos:", movimientos_activos)
                    for i, mov in enumerate(movimientos_activos):
                        print(f"  Mov {i+1}: Debe={mov.debe}, Haber={mov.haber}")

                    if abs(total_debe - total_haber) > 0.01:  # Usar tolerancia de 0.01
                        raise ValidationError('La transacción no está balanceada. El total del Debe debe ser igual al total del Haber.')
                    
                    # NO sobrescribir el monto si ya está establecido
                    if not transaccion.monto_total or transaccion.monto_total == 0:
                        transaccion.monto_total = round(total_debe, 2)
                        transaccion.save()
                    
                    # NO sobrescribir el monto del documento si ya está establecido
                    if not documento_banco.monto or documento_banco.monto == 0:
                        documento_banco.monto = round(total_debe, 2)
                        documento_banco.save()
                
                messages.success(request, 'El documento bancario y la transacción han sido actualizados correctamente.')
                return redirect('documentobanco_list')
            
            except Exception as e:
                # Mostrar errores específicos en consola para depuración
                print(f"Error al guardar: {str(e)}")
                return render_error_response(f'Error al guardar: {str(e)}')
            
        else:
            # Mostrar errores específicos en consola para depuración
            if not documento_form.is_valid():
                print("Errores en DocumentoBancoForm:", documento_form.errors)
            
            if not transaccion_form.is_valid():
                print("Errores en TransaccionForm:", transaccion_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)
            
            return render_error_response('Por favor, corrige los errores en el formulario.')

class EliminarDocumentoBancoView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        documento = get_object_or_404(DocumentoBanco, pk=pk)
        
        if not documento.activo:
            messages.warning(request, 'El documento bancario ya está desactivado.')
            return redirect('documentobanco_list')
        
        documento.desactivar()
        
        messages.success(request, f'El documento bancario {documento.numero_documento} ha sido desactivado correctamente.')
        return redirect('documentobanco_list')    