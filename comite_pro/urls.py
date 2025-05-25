"""
URL configuration for comite_pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('empresa/', include('empresa.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('catalogos/', include('catalogo_cuentas.urls')),
    path('documentos/', include('documentos.urls')),
    path('transacciones/', include('transacciones.urls')),
    path('bancos/', include('bancos.urls')),
    path('reportes/', include('reportes.urls')),
    path('terceros/', include('terceros.urls')),
    path('', RedirectView.as_view(url='/usuarios/login/')),  # Redirige a la URL de login
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
