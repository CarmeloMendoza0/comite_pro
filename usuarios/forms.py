#comite_pro/usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group

class CustomUserCreationForm(UserCreationForm):
    rol = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Selecciona el rol",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        """Sobrescribir save para asignar el grupo/rol"""
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Asignar el grupo seleccionado
            rol = self.cleaned_data.get('rol')
            if rol:
                user.groups.add(rol)
        
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
