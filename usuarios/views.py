# comite_pro/usuarios/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import user_passes_test
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User, Group
from django.views.generic import ListView, UpdateView
from django import forms
from django.contrib import messages

def is_admin(user):
    return user.groups.filter(name='administrador').exists()

def is_accountant(user):
    return user.groups.filter(name='contable').exists()

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'

    def dispatch(self, request, *args, **kwargs):
        # Si el usuario ya está autenticado, redirigirlo al dashboard
        if request.user.is_authenticated:
            return redirect('empresa_list')  # Redirigir a la vista o página deseada
        return super().dispatch(request, *args, **kwargs)
    
# Decorador aplicado para verificar si el usuario es administrador
@method_decorator(user_passes_test(is_admin), name='dispatch')
class RegistrarUsuarioView(LoginRequiredMixin, generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = 'usuarios/registrar_usuario.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Guardar el usuario sin cometer a la base de datos
        user = form.save(commit=False)
        user.save()

        # Asignar grupo (rol) al usuario
        rol = form.cleaned_data.get('rol')
        if rol:
            group = Group.objects.get(name=rol)
            user.groups.add(group)

        return super().form_valid(form)

@method_decorator(user_passes_test(is_admin), name='dispatch')
class ListaUsuariosView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'usuarios/usuarios_list.html'
    context_object_name = 'usuarios'

# Decorador aplicado para verificar si el usuario es administrador
@method_decorator(user_passes_test(is_admin), name='dispatch')
class EditarUsuarioCompletoView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'usuarios/form_usuario.html'
    fields = ['username', 'password', 'groups']
    success_url = reverse_lazy('usuarios_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Personalización de campos de formulario
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control'})
        form.fields['groups'].queryset = Group.objects.all()
        form.fields['groups'].label = "Roles"
        form.fields['groups'].widget.attrs.update({'class': 'form-control'})
        
        return form

    def form_valid(self, form):
        user = form.save(commit=False)
        
        ## Encriptar la contraseña antes de guardar solo si se ha cambiado
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        return super().form_valid(form)