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


class RegistroDocumentoBancoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        documento_form = DocumentoBancoForm()
        transaccion_form = TransaccionForm()
        movimiento_formset = MovimientoFormSet()
        cuentas = Cuenta.objects.filter(nivel=3)  
        
        return render(request, 'bancos/documentobanco_form.html', {
            'documento_form': documento_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,  # Pasa las cuentas al contexto
            'is_edit': False,
            'titulo': 'Registrar Documento Bancario',
        })

    def post(self, request, *args, **kwargs):
        documento_form = DocumentoBancoForm(request.POST)
        transaccion_form = TransaccionForm(request.POST)
        movimiento_formset = MovimientoFormSet(request.POST)
        cuentas = Cuenta.objects.filter(nivel=3)

        # Obtener el tipo de movimiento del formulario
        tipo_movimiento = request.POST.get('tipo_movimiento')

        # Validar los formularios
        if documento_form.is_valid() and transaccion_form.is_valid() and movimiento_formset.is_valid():
            # Validar que el Debe y el Haber estén correctamente llenos antes de guardar
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        messages.error(request, 'Debe ingresar un valor en Debe o en Haber, pero no en ambos.')
                        return render(request, 'bancos/documentobanco_form.html', {
                            'documento_form': documento_form,
                            'transaccion_form': transaccion_form,
                            'movimiento_formset': movimiento_formset,
                            'cuentas': cuentas,
                            'is_edit': False,
                            'titulo': 'Registrar Documento Bancario',
                        })
                    
            # Validar que el periodo contable esté abierto
            periodo = transaccion_form.cleaned_data.get('periodo')
            if not periodo:
                messages.error(request, 'Debe seleccionar un periodo para la transacción.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': False,
                    'titulo': 'Registrar Documento Bancario',
                })
            elif periodo.estado != 'Abierto':
                messages.error(request, 'El periodo contable está cerrado. No puede realizar operaciones.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': False,
                    'titulo': 'Registrar Documento Bancario',
                })

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
                messages.error(request, f'Error al guardar: {str(e)}')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': False,
                    'titulo': 'Registrar Documento Bancario',
                })
        else:
            # Mostrar errores específicos en consola para depuración
            if not documento_form.is_valid():
                print("Errores en DocumentoBancoForm:", documento_form.errors)
            
            if not transaccion_form.is_valid():
                print("Errores en TransaccionForm:", transaccion_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)

            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            return render(request, 'bancos/documentobanco_form.html', {
                'documento_form': documento_form,
                'transaccion_form': transaccion_form,
                'movimiento_formset': movimiento_formset,
                'cuentas' : cuentas,
                'is_edit': False,
                'titulo': 'Registrar Documento Bancario',
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
        documento_form = DocumentoBancoForm(instance=documento_banco, initial=initial_data)
        transaccion_form = TransaccionForm(instance=transaccion, initial={'fecha': transaccion.fecha.strftime('%Y-%m-%d') if transaccion.fecha else None})
        movimiento_formset = MovimientoFormSet(instance=transaccion)

        # Obtener lista de cuentas disponibles
        cuentas = Cuenta.objects.filter(nivel=3)

        # Calcular totales para mostrarlos inicialmente
        movimientos = Movimiento.objects.filter(transaccion=transaccion)
        total_debe = sum(mov.debe or 0 for mov in movimientos)
        total_haber = sum(mov.haber or 0 for mov in movimientos)

        return render(request, 'bancos/documentobanco_form.html', {
            'documento_form': documento_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': True,  # Indicador de modo edición
            'titulo': 'Editar Documento Bancario',
            'total_debe': total_debe,
            'total_haber': total_haber,
        })
    
    def post(self, request, pk, *args, **kwargs):
        # Obtener instancias existentes
        documento_banco = get_object_or_404(DocumentoBanco, pk=pk)
        transaccion = Transaccion.objects.filter(banco=documento_banco).first()
        
        if not transaccion:
            messages.error(request, 'No se encontró una transacción asociada a este documento bancario.')
            return redirect('documentobanco_list')
        
        # Inicializar formularios con datos del POST e instancias existentes
        documento_form = DocumentoBancoForm(request.POST, instance=documento_banco)
        transaccion_form = TransaccionForm(request.POST, instance=transaccion)
        movimiento_formset = MovimientoFormSet(request.POST, instance=transaccion)

        cuentas = Cuenta.objects.filter(nivel=3)

        # Obtener el tipo de movimiento del formulario
        tipo_movimiento = request.POST.get('tipo_movimiento')   

        # Validar formularios
        if documento_form.is_valid() and transaccion_form.is_valid() and movimiento_formset.is_valid():
            # Validaciones adicionales antes de la transacción
            # Verificar debe/haber
            for form in movimiento_formset:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    debe = form.cleaned_data.get('debe', 0) or 0
                    haber = form.cleaned_data.get('haber', 0) or 0
                    if (debe and haber) or (not debe and not haber):
                        messages.error(request, 'Debe ingresar un valor en Debe o en Haber, pero no en ambos.')
                        return render(request, 'bancos/documentobanco_form.html', {
                            'documento_form': documento_form,
                            'transaccion_form': transaccion_form,
                            'movimiento_formset': movimiento_formset,
                            'cuentas': cuentas,
                            'is_edit': True,
                            'titulo': 'Editar Documento Bancario',
                        })
                    
            # Verificar periodo contable
            periodo = transaccion_form.cleaned_data.get('periodo')
            if not periodo:
                messages.error(request, 'Debe seleccionar un periodo para la transacción.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': True,
                    'titulo': 'Editar Documento Bancario',
                })
            elif periodo.estado != 'Abierto':
                messages.error(request, 'El periodo contable está cerrado. No puede realizar operaciones.')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': True,
                    'titulo': 'Editar Documento Bancario',
                })
            
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

                    if total_debe != total_haber:
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
                
                messages.error(request, f'Error al guardar: {str(e)}')
                return render(request, 'bancos/documentobanco_form.html', {
                    'documento_form': documento_form,
                    'transaccion_form': transaccion_form,
                    'movimiento_formset': movimiento_formset,
                    'cuentas': cuentas,
                    'is_edit': True,
                    'titulo': 'Editar Documento Bancario',
                })
                
        else:
            # Mostrar errores específicos en consola para depuración
            if not documento_form.is_valid():
                print("Errores en DocumentoBancoForm:", documento_form.errors)
            
            if not transaccion_form.is_valid():
                print("Errores en TransaccionForm:", transaccion_form.errors)
            
            if not movimiento_formset.is_valid():
                print("Errores en MovimientoFormSet:", movimiento_formset.errors)
            
            messages.error(request, 'Por favor, corrige los errores en el formulario.')

        return render(request, 'bancos/documentobanco_form.html', {
            'documento_form': documento_form,
            'transaccion_form': transaccion_form,
            'movimiento_formset': movimiento_formset,
            'cuentas': cuentas,
            'is_edit': True,
            'titulo': 'Editar Documento Bancario',
        })    