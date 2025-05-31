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

from django.views.generic import TemplateView
from transacciones.models import Transaccion
from catalogo_cuentas.models import Cuenta
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'empresa/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener empresa del usuario actual
        # Suponemos que el usuario puede estar en múltiples empresas
        # y obtenemos la primera de ellas para simplicidad
        empresa_actual = self.request.user.empresa.first()
        
        # Si no hay empresa, devolver contexto vacío
        if not empresa_actual:
            context.update({
                'empresa_actual': None,
                'total_ingresos': 0,
                'total_gastos': 0,
                'total_donaciones': 0,
                'saldo_actual': 0,
                'porcentaje_ingresos': 0,
                'porcentaje_gastos': 0,
                'porcentaje_donaciones': 0,
                'porcentaje_saldo': 0,
                'ultimas_transacciones': [],
                'meses': json.dumps([]),
                'datos_ingresos': json.dumps([]),
                'datos_gastos': json.dumps([]),
                'categorias_gastos': json.dumps([]),
                'datos_categorias_gastos': json.dumps([]),
            })
            return context
        
        # Fechas para cálculos
        hoy = timezone.now().date()
        inicio_mes_actual = hoy.replace(day=1)
        fin_mes_actual = (inicio_mes_actual + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Calcular el mes anterior
        if inicio_mes_actual.month == 1:
            inicio_mes_anterior = datetime(inicio_mes_actual.year - 1, 12, 1).date()
            fin_mes_anterior = datetime(inicio_mes_actual.year - 1, 12, 31).date()
        else:
            inicio_mes_anterior = datetime(inicio_mes_actual.year, inicio_mes_actual.month - 1, 1).date()
            fin_mes_anterior = (inicio_mes_actual - timedelta(days=1))
        
        # Obtener transacciones del mes actual
        transacciones_mes_actual = Transaccion.objects.filter(
            empresa=empresa_actual,
            fecha__gte=inicio_mes_actual,
            fecha__lte=fin_mes_actual,
            activo=True  # Solo transacciones activas
        ).exclude(
            # Excluir transacciones vinculadas a DocumentoBanco inactivos
            banco__activo=False
        ).exclude(
            # Excluir transacciones vinculadas a DocComprobante inactivos o anulados
            comprobante__activo=False
        ).exclude(
            comprobante__estado='Anulado'
        )
        
        # Obtener transacciones del mes anterior
        transacciones_mes_anterior = Transaccion.objects.filter(
            empresa=empresa_actual,
            fecha__gte=inicio_mes_anterior,
            fecha__lte=fin_mes_anterior,
            activo=True  # Solo transacciones activas
        ).exclude(
            # Excluir transacciones vinculadas a DocumentoBanco inactivos
            banco__activo=False
        ).exclude(
            # Excluir transacciones vinculadas a DocComprobante inactivos o anulados
            comprobante__activo=False
        ).exclude(
            comprobante__estado='Anulado'
        )
        
        # Calcular totales del mes actual
        ingresos_mes_actual = transacciones_mes_actual.filter(
            tipo_transaccion='Ingreso'
        ).aggregate(total=Sum('monto_total'))['total'] or 0
        
        gastos_mes_actual = transacciones_mes_actual.filter(
            tipo_transaccion='Egreso'
        ).aggregate(total=Sum('monto_total'))['total'] or 0
        
        # Identificar donaciones (asumimos que hay una cuenta específica para donaciones)
        # Para esto necesitaríamos identificar las cuentas de donaciones
        # Aquí como ejemplo usamos los movimientos que tienen la palabra "donación" en la descripción
        donaciones_mes_actual = transacciones_mes_actual.filter(
            descripcion__icontains='donación',
            tipo_transaccion='Ingreso'
        ).aggregate(total=Sum('monto_total'))['total'] or 0
        
        # Calcular totales del mes anterior para comparación
        ingresos_mes_anterior = transacciones_mes_anterior.filter(
            tipo_transaccion='Ingreso'
        ).aggregate(total=Sum('monto_total'))['total'] or 0
        
        gastos_mes_anterior = transacciones_mes_anterior.filter(
            tipo_transaccion='Egreso'
        ).aggregate(total=Sum('monto_total'))['total'] or 0
        
        donaciones_mes_anterior = transacciones_mes_anterior.filter(
            descripcion__icontains='donación',
            tipo_transaccion='Ingreso'
        ).aggregate(total=Sum('monto_total'))['total'] or 0
        
        # Calcular porcentajes de cambio
        if ingresos_mes_anterior > 0:
            porcentaje_ingresos = ((ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior) * 100
        else:
            porcentaje_ingresos = 100 if ingresos_mes_actual > 0 else 0
            
        if gastos_mes_anterior > 0:
            porcentaje_gastos = ((gastos_mes_actual - gastos_mes_anterior) / gastos_mes_anterior) * 100
        else:
            porcentaje_gastos = 100 if gastos_mes_actual > 0 else 0
            
        if donaciones_mes_anterior > 0:
            porcentaje_donaciones = ((donaciones_mes_actual - donaciones_mes_anterior) / donaciones_mes_anterior) * 100
        else:
            porcentaje_donaciones = 100 if donaciones_mes_actual > 0 else 0
        
        # Calcular saldo actual (suponemos que es la diferencia entre ingresos y gastos acumulados)
        saldo_mes_actual = ingresos_mes_actual - gastos_mes_actual
        saldo_mes_anterior = ingresos_mes_anterior - gastos_mes_anterior
        
        if saldo_mes_anterior > 0:
            porcentaje_saldo = ((saldo_mes_actual - saldo_mes_anterior) / saldo_mes_anterior) * 100
        else:
            porcentaje_saldo = 100 if saldo_mes_actual > 0 else 0
        
        # Obtener las últimas transacciones
        ultimas_transacciones = Transaccion.objects.filter(
            empresa=empresa_actual,
            activo=True  # Solo transacciones activas
        ).exclude(
            # Excluir transacciones vinculadas a DocumentoBanco inactivos
            banco__activo=False
        ).exclude(
            # Excluir transacciones vinculadas a DocComprobante inactivos o anulados
            comprobante__activo=False
        ).exclude(
            comprobante__estado='Anulado'
        ).order_by('-fecha')[:10]
        
        # Datos para el gráfico de ingresos vs gastos (últimos 6 meses)
        meses = []
        datos_ingresos = []
        datos_gastos = []
        
        for i in range(5, -1, -1):
            # Calcular el mes
            if hoy.month - i <= 0:
                mes = hoy.month - i + 12
                año = hoy.year - 1
            else:
                mes = hoy.month - i
                año = hoy.year
                
            fecha_inicio = datetime(año, mes, 1).date()
            if mes == 12:
                fecha_fin = datetime(año, mes, 31).date()
            else:
                fecha_fin = datetime(año, mes + 1, 1).date() - timedelta(days=1)
            
            # Nombres de los meses en español
            nombres_meses = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]
            meses.append(nombres_meses[mes - 1])
            
            # Calcular ingresos y gastos para el mes
            ingresos_mes = Transaccion.objects.filter(
                empresa=empresa_actual,
                tipo_transaccion='Ingreso',
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin,
                activo=True  # Solo transacciones activas
            ).exclude(
                banco__activo=False
            ).exclude(
                comprobante__activo=False
            ).exclude(
                comprobante__estado='Anulado'
            ).aggregate(total=Sum('monto_total'))['total'] or 0
            
            gastos_mes = Transaccion.objects.filter(
                empresa=empresa_actual,
                tipo_transaccion='Egreso',
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin,
                activo=True  # Solo transacciones activas
            ).exclude(
                banco__activo=False
            ).exclude(
                comprobante__activo=False
            ).exclude(
                comprobante__estado='Anulado'
            ).aggregate(total=Sum('monto_total'))['total'] or 0
            
            # Convertir Decimal a float para serialización JSON
            datos_ingresos.append(float(ingresos_mes))
            datos_gastos.append(float(gastos_mes))
        
        # Datos para el gráfico de distribución de gastos
        # Aquí asumimos que podemos categorizar gastos por el primer nivel de cuentas contables
        # o por tipos de documentos
        categorias_gastos = []
        datos_categorias_gastos = []
        
        # Obtener gastos por tipo de documento
        gastos_por_tipo = Transaccion.objects.filter(
            empresa=empresa_actual,
            tipo_transaccion='Egreso',
            fecha__gte=inicio_mes_actual,
            fecha__lte=fin_mes_actual,
            tipo_documento__isnull=False,
            activo=True  # Solo transacciones activas
        ).exclude(
            banco__activo=False
        ).exclude(
            comprobante__activo=False
        ).exclude(
            comprobante__estado='Anulado'
        ).values('tipo_documento__nombre').annotate(total=Sum('monto_total'))
        
        for item in gastos_por_tipo:
            categorias_gastos.append(item['tipo_documento__nombre'])
            datos_categorias_gastos.append(float(item['total']))
        
        #Categoría por defecto
        if not categorias_gastos:
            categorias_gastos = ['Sin categorizar', 'Operativos', 'Administrativos', 'Financieros', 'Otros']
            datos_categorias_gastos = [0, 80, 25, 0, 0]  # valores por defecto de ejemplo
            
        # Actualizar el contexto con todos los datos calculados
        context.update({
            'empresa_actual': empresa_actual,
            'total_ingresos': ingresos_mes_actual,
            'total_gastos': gastos_mes_actual,
            'total_donaciones': donaciones_mes_actual,
            'saldo_actual': saldo_mes_actual,
            'porcentaje_ingresos': porcentaje_ingresos,
            'porcentaje_gastos': porcentaje_gastos,
            'porcentaje_donaciones': porcentaje_donaciones,
            'porcentaje_saldo': porcentaje_saldo,
            'ultimas_transacciones': ultimas_transacciones,
            'meses': json.dumps(meses),
            'datos_ingresos': json.dumps(datos_ingresos),
            'datos_gastos': json.dumps(datos_gastos),
            'categorias_gastos': json.dumps(categorias_gastos),
            'datos_categorias_gastos': json.dumps(datos_categorias_gastos),
        })
        
        return context

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
        context['title'] = 'Crear Nueva Organización'
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
        context['title'] = 'Editar Organización'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')    
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
        context['title'] = 'Datos de la Organización'
        return context

@method_decorator(user_passes_test(is_admin), name='dispatch')
class PeriodoContableCreateView(LoginRequiredMixin, generic.CreateView):
    model = PeriodoContable
    form_class = PeriodoContableForm
    template_name = "empresa/periodos_form.html"
    success_url = reverse_lazy('lista_periodos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Período Contable'
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
        context['title'] = 'Lista de Períodos Contables'
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