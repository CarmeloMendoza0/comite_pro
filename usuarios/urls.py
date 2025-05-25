#comite_pro/usuarios/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RegistrarUsuarioView, CustomLoginView, ListaUsuariosView, EditarUsuarioCompletoView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),  
    path('registro/', RegistrarUsuarioView.as_view(), name="registrar"),
    path('', ListaUsuariosView.as_view(), name="usuarios_list"),
    path('editar/<int:pk>/', EditarUsuarioCompletoView.as_view(), name="editar_usuario"),
]
