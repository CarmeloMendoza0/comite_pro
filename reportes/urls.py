# comite_pro/reportes/urls.py
from django.urls import path
from .views import (
    LibroDiarioView, 
    ExportarLibroDiarioPDFView, 
    LibroMayorView, 
    ExportarLibroMayorPDFView,
    ExportarLibroDiarioExcelView,
    ExportarLibroMayorExcelView  
)
urlpatterns = [
    path('libro-diario/', LibroDiarioView.as_view(), name='libro_diario'),
    path('libro-diario-pdf/', ExportarLibroDiarioPDFView.as_view(), name='exportar_libro_diario_pdf'),
    path('libro-diario-excel/', ExportarLibroDiarioExcelView.as_view(), name='exportar_libro_diario_excel'),
    path('libro-mayor/', LibroMayorView.as_view(), name='libro_mayor'),
    path('libro-mayor-pdf/', ExportarLibroMayorPDFView.as_view(), name='exportar_libro_mayor_pdf'),
    path('libro-mayor-excel/', ExportarLibroMayorExcelView.as_view(), name='exportar_libro_mayor_excel'),
]


