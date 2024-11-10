#  comite_pro/reportes/views.py
from django.shortcuts import render
from django.views import View
from transacciones.models import Transaccion, Movimiento
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from catalogo_cuentas.models import Cuenta

class LibroDiarioView(LoginRequiredMixin, View):
    def get(self, request):
        # Filtrar transacciones por empresa y ordenar por fecha
        empresa = request.user.empresa.first()
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        transacciones = Transaccion.objects.filter(empresa=empresa).order_by('fecha')

        if fecha_inicio:
            transacciones = transacciones.filter(fecha__gte=parse_date(fecha_inicio))
        if fecha_fin:
            transacciones = transacciones.filter(fecha__lte=parse_date(fecha_fin))

        # Lista para almacenar los datos del reporte
        reporte_data = []

        for transaccion in transacciones:
            movimientos = Movimiento.objects.filter(transaccion=transaccion)
            total_debe = sum(movimiento.debe for movimiento in movimientos)
            total_haber = sum(movimiento.haber for movimiento in movimientos)
            reporte_data.append({
                'fecha': transaccion.fecha,
                'descripcion': transaccion.descripcion,
                'transaccion': transaccion,
                'movimientos': movimientos,
                'total_debe': total_debe,
                'total_haber': total_haber
            })

        context = {
            'reporte_data': reporte_data,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
        }

        return render(request, 'reportes/libro_diario.html', context)

class ExportarLibroDiarioPDFView(LoginRequiredMixin, View):
    def get(self, request):
        # Utilizar la misma lógica de filtro que la vista anterior
        empresa = request.user.empresa.first()
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        # Inicializar el queryset vacío
        transacciones = Transaccion.objects.filter(empresa=empresa).order_by('fecha') if empresa else Transaccion.objects.none()

        # Verificar si las fechas son válidas antes de filtrar
        if fecha_inicio:
            fecha_inicio = parse_date(fecha_inicio)
            if fecha_inicio:
                transacciones = transacciones.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            fecha_fin = parse_date(fecha_fin)
            if fecha_fin:
                transacciones = transacciones.filter(fecha__lte=fecha_fin)    

        # Lista para almacenar los datos del reporte
        reporte_data = []

        for transaccion in transacciones:
            movimientos = Movimiento.objects.filter(transaccion=transaccion)
            total_debe = sum(movimiento.debe for movimiento in movimientos)
            total_haber = sum(movimiento.haber for movimiento in movimientos)
            reporte_data.append({
                'fecha': transaccion.fecha,
                'descripcion': transaccion.descripcion,
                'transaccion': transaccion,
                'movimientos': movimientos,
                'total_debe': total_debe,
                'total_haber': total_haber
            })

        # Cargar la plantilla HTML y generar el PDF
        template = get_template('reportes/libro_diario_pdf.html')
        html_content = template.render({'reporte_data': reporte_data, 'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin})
        pdf_file = HTML(string=html_content).write_pdf()

        # Responder con el archivo PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="libro_diario.pdf"'
        return response
    

class LibroMayorView(LoginRequiredMixin, View):
    def get(self, request):
        # Filtrar cuentas por empresa
        empresa = request.user.empresa.first()
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        cuenta_codigo = request.GET.get('cuenta')

        # Filtrar cuentas de la empresa
        cuentas = Cuenta.objects.filter(catalogo__empresa=empresa)
        reporte_data = []

        # Filtrar movimientos por cuenta seleccionada o todas las cuentas
        if cuenta_codigo:
            cuentas = cuentas.filter(codigo=cuenta_codigo)

        for cuenta in cuentas:
            # Calcular el saldo acumulado hasta antes de la fecha de inicio
            saldo_anterior = cuenta.saldo
            if fecha_inicio:
                movimientos_antes = Movimiento.objects.filter(
                    cuenta=cuenta,
                    transaccion__fecha__lt=parse_date(fecha_inicio)
                ).order_by('transaccion__fecha')

                # Calcular el saldo antes de la fecha de inicio
                for movimiento in movimientos_antes:
                    if cuenta.catalogo.tipo in ['Activo', 'Gasto']:  # Naturaleza deudora
                        saldo_anterior += movimiento.debe
                        saldo_anterior -= movimiento.haber
                    elif cuenta.catalogo.tipo in ['Pasivo', 'Capital', 'Ingreso']:  # Naturaleza acreedora
                        saldo_anterior -= movimiento.debe
                        saldo_anterior += movimiento.haber

            # Obtener los movimientos a partir de la fecha de inicio hasta la fecha fin
            movimientos = Movimiento.objects.filter(cuenta=cuenta).order_by('transaccion__fecha')
            if fecha_inicio:
                movimientos = movimientos.filter(transaccion__fecha__gte=parse_date(fecha_inicio))
            if fecha_fin:
                movimientos = movimientos.filter(transaccion__fecha__lte=parse_date(fecha_fin))

            movimientos_data = []
            total_debe = 0
            total_haber = 0
            saldo_actual = saldo_anterior

             # Calcular el saldo para cada movimiento y total de debe/haber
            for movimiento in movimientos:
                saldo_anterior_actual = saldo_actual
                if cuenta.catalogo.tipo in ['Activo', 'Gasto']:  # Naturaleza deudora
                    saldo_actual += movimiento.debe
                    saldo_actual -= movimiento.haber
                elif cuenta.catalogo.tipo in ['Pasivo', 'Capital', 'Ingreso']:  # Naturaleza acreedora
                    saldo_actual -= movimiento.debe
                    saldo_actual += movimiento.haber

                
                total_debe += movimiento.debe
                total_haber += movimiento.haber

                movimientos_data.append({
                    'fecha': movimiento.transaccion.fecha,
                    'descripcion': movimiento.transaccion.descripcion,
                    'saldo_anterior': saldo_anterior_actual,
                    'debe': movimiento.debe,
                    'haber': movimiento.haber,
                    'saldo': saldo_actual
                })

            reporte_data.append({
                'codigo_cuenta': cuenta.codigo,
                'nombre_cuenta': cuenta.nombre,
                'saldo_anterior': saldo_anterior,
                'movimientos': movimientos_data,
                'total_debe': total_debe,
                'total_haber': total_haber,
                'saldo_final': saldo_actual
            })

        context = {
            'reporte_data': reporte_data,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'cuentas': cuentas,
            'cuenta_seleccionada': cuenta_codigo,
        }

        return render(request, 'reportes/libro_mayor.html', context)
    

class ExportarLibroMayorPDFView(LoginRequiredMixin, View):
    def get(self, request):
        # Filtrar cuentas por empresa
        empresa = request.user.empresa.first()
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        cuenta_codigo = request.GET.get('cuenta')

        # Filtrar cuentas de la empresa
        cuentas = Cuenta.objects.filter(catalogo__empresa=empresa)
        reporte_data = []

        # Filtrar movimientos por cuenta seleccionada o todas las cuentas
        if cuenta_codigo:
            cuentas = cuentas.filter(codigo=cuenta_codigo)

        for cuenta in cuentas:
            # Calcular el saldo acumulado hasta antes de la fecha de inicio
            saldo_anterior = cuenta.saldo
            if fecha_inicio:
                movimientos_antes = Movimiento.objects.filter(
                    cuenta=cuenta,
                    transaccion__fecha__lt=parse_date(fecha_inicio)
                ).order_by('transaccion__fecha')

                # Calcular el saldo antes de la fecha de inicio
                for movimiento in movimientos_antes:
                    if cuenta.catalogo.tipo in ['Activo', 'Gasto']:  # Naturaleza deudora
                        saldo_anterior += movimiento.debe
                        saldo_anterior -= movimiento.haber
                    elif cuenta.catalogo.tipo in ['Pasivo', 'Capital', 'Ingreso']:  # Naturaleza acreedora
                        saldo_anterior -= movimiento.debe
                        saldo_anterior += movimiento.haber

            # Obtener los movimientos a partir de la fecha de inicio hasta la fecha fin
            movimientos = Movimiento.objects.filter(cuenta=cuenta).order_by('transaccion__fecha')
            if fecha_inicio:
                movimientos = movimientos.filter(transaccion__fecha__gte=parse_date(fecha_inicio))
            if fecha_fin:
                movimientos = movimientos.filter(transaccion__fecha__lte=parse_date(fecha_fin))

            movimientos_data = []
            total_debe = 0
            total_haber = 0
            saldo_actual = saldo_anterior

             # Calcular el saldo para cada movimiento y total de debe/haber
            for movimiento in movimientos:
                saldo_anterior_actual = saldo_actual
                if cuenta.catalogo.tipo in ['Activo', 'Gasto']:  # Naturaleza deudora
                    saldo_actual += movimiento.debe
                    saldo_actual -= movimiento.haber
                elif cuenta.catalogo.tipo in ['Pasivo', 'Capital', 'Ingreso']:  # Naturaleza acreedora
                    saldo_actual -= movimiento.debe
                    saldo_actual += movimiento.haber

                
                total_debe += movimiento.debe
                total_haber += movimiento.haber

                movimientos_data.append({
                    'fecha': movimiento.transaccion.fecha,
                    'descripcion': movimiento.transaccion.descripcion,
                    'saldo_anterior': saldo_anterior_actual,
                    'debe': movimiento.debe,
                    'haber': movimiento.haber,
                    'saldo': saldo_actual
                })

            reporte_data.append({
                'codigo_cuenta': cuenta.codigo,
                'nombre_cuenta': cuenta.nombre,
                'saldo_anterior': saldo_anterior,
                'movimientos': movimientos_data,
                'total_debe': total_debe,
                'total_haber': total_haber,
                'saldo_final': saldo_actual
            })

        context = {
            'reporte_data': reporte_data,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'cuentas': cuentas,
            'cuenta_seleccionada': cuenta_codigo,
        }

        # Cargar la plantilla HTML y generar el PDF
        template = get_template('reportes/libro_mayor_pdf.html')
        html_content = template.render(context)
        pdf_file = HTML(string=html_content).write_pdf()

        # Responder con el archivo PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="libro_mayor.pdf"'
        return response