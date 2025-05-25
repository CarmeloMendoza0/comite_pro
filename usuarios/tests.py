from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.urls import reverse
from django.core.exceptions import ValidationError

from .forms import CustomUserCreationForm, CustomAuthenticationForm

class UsuarioTestCase(TestCase):
    """
    Pruebas para la creación y autenticación de usuarios
    Basado en Tabla 24: Datos Ingresados en la Prueba de Creación de Usuario
    """
    
    def setUp(self):
        """Configuración inicial para todas las pruebas"""
        self.client = Client()
        
        # Crear grupos/roles de prueba
        self.grupo_admin = Group.objects.create(name="Administrador")
        self.grupo_contador = Group.objects.create(name="Contador")
        self.grupo_usuario = Group.objects.create(name="Usuario")
        
        # Datos de usuario de prueba
        self.datos_usuario = {
            'username': 'usuario_prueba',
            'password1': 'MiPassword123!',
            'password2': 'MiPassword123!',
            'rol': self.grupo_contador.id
        }

    def test_creacion_usuario_exitosa(self):
        """Test: Creación exitosa de usuario con datos válidos"""
        form = CustomUserCreationForm(data=self.datos_usuario)
        
        # Verificar que el formulario es válido
        self.assertTrue(form.is_valid(), f"Errores del formulario: {form.errors}")
        
        # Guardar usuario
        usuario = form.save()
        
        # Verificaciones básicas
        self.assertEqual(usuario.username, 'usuario_prueba')
        self.assertTrue(usuario.check_password('MiPassword123!'))
        self.assertTrue(usuario.is_active)
        
        # Verificar asignación de rol
        self.assertIn(self.grupo_contador, usuario.groups.all())

    def test_validacion_confirmacion_password(self):
        """Test: Validación de confirmación de contraseña"""
        datos_invalidos = self.datos_usuario.copy()
        datos_invalidos['password2'] = 'PasswordDiferente123!'
        
        form = CustomUserCreationForm(data=datos_invalidos)
        
        # El formulario debe ser inválido
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_validacion_username_unico(self):
        """Test: Validación de nombre de usuario único"""
        # Crear primer usuario
        User.objects.create_user(
            username='usuario_existente',
            password='Password123!'
        )
        
        # Intentar crear segundo usuario con mismo username
        datos_duplicados = self.datos_usuario.copy()
        datos_duplicados['username'] = 'usuario_existente'
        
        form = CustomUserCreationForm(data=datos_duplicados)
        
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_validacion_password_complejo(self):
        """Test: Validación de complejidad de contraseña"""
        passwords_invalidos = [
            '123456',      # Muy simple
            'password',    # Sin números
            '12345678',    # Solo números
            'abc',         # Muy corto
        ]
        
        for password_invalido in passwords_invalidos:
            datos_test = self.datos_usuario.copy()
            datos_test['password1'] = password_invalido
            datos_test['password2'] = password_invalido
            
            form = CustomUserCreationForm(data=datos_test)
            
            self.assertFalse(form.is_valid(), 
                            f"Password '{password_invalido}' debería ser inválido")

    def test_asignacion_roles_diferentes(self):
        """Test: Asignación de diferentes roles a usuarios"""
        roles_test = [
            (self.grupo_admin, "Administrador"),
            (self.grupo_contador, "Contador"), 
            (self.grupo_usuario, "Usuario")
        ]
        
        for i, (grupo, nombre_rol) in enumerate(roles_test):
            datos_usuario = {
                'username': f'usuario_{nombre_rol.lower()}_{i}',
                'password1': 'TestPassword123!',
                'password2': 'TestPassword123!',
                'rol': grupo.id
            }
            
            form = CustomUserCreationForm(data=datos_usuario)
            self.assertTrue(form.is_valid())
            
            usuario = form.save()
            self.assertIn(grupo, usuario.groups.all())

    def test_formulario_autenticacion(self):
        """Test: Formulario de autenticación personalizado"""
        # Crear usuario para autenticación
        usuario = User.objects.create_user(
            username='test_login',
            password='LoginPassword123!'
        )
        
        # Datos de login válidos
        datos_login = {
            'username': 'test_login',
            'password': 'LoginPassword123!'
        }
        
        form = CustomAuthenticationForm(data=datos_login)
        self.assertTrue(form.is_valid())

    def test_autenticacion_exitosa(self):
        """Test: Autenticación exitosa de usuario"""
        # Crear usuario
        usuario = User.objects.create_user(
            username='usuario_auth',
            password='AuthPassword123!'
        )
        
        # Intentar autenticación
        usuario_autenticado = authenticate(
            username='usuario_auth',
            password='AuthPassword123!'
        )
        
        self.assertIsNotNone(usuario_autenticado)
        self.assertEqual(usuario_autenticado.username, 'usuario_auth')

    def test_autenticacion_fallida(self):
        """Test: Autenticación fallida con credenciales incorrectas"""
        # Crear usuario
        User.objects.create_user(
            username='usuario_test',
            password='CorrectPassword123!'
        )
        
        # Intentar autenticación con password incorrecta
        usuario_autenticado = authenticate(
            username='usuario_test',
            password='PasswordIncorrecto123!'
        )
        
        self.assertIsNone(usuario_autenticado)

    def test_campos_formulario_usuario(self):
        """Test: Verificación de campos del formulario de usuario"""
        form = CustomUserCreationForm()
        
        # Verificar que los campos esperados estén presentes
        campos_esperados = ['username', 'password1', 'password2', 'rol']
        for campo in campos_esperados:
            self.assertIn(campo, form.fields)

    def test_usuario_inactivo(self):
        """Test: Comportamiento con usuario inactivo"""
        # Crear usuario inactivo
        usuario = User.objects.create_user(
            username='usuario_inactivo',
            password='Password123!',
            is_active=False
        )
        
        # La autenticación debe fallar para usuario inactivo
        usuario_autenticado = authenticate(
            username='usuario_inactivo',
            password='Password123!'
        )
        
        self.assertIsNone(usuario_autenticado)

    def test_multiples_grupos_usuario(self):
        """Test: Usuario puede pertenecer a múltiples grupos"""
        # Crear usuario
        usuario = User.objects.create_user(
            username='usuario_multi_rol',
            password='Password123!'
        )
        
        # Asignar múltiples grupos
        usuario.groups.add(self.grupo_contador)
        usuario.groups.add(self.grupo_usuario)
        
        # Verificar asignaciones
        self.assertEqual(usuario.groups.count(), 2)
        self.assertIn(self.grupo_contador, usuario.groups.all())
        self.assertIn(self.grupo_usuario, usuario.groups.all())

    def test_validacion_rol_requerido(self):
        """Test: Validación de rol requerido en formulario"""
        datos_sin_rol = self.datos_usuario.copy()
        del datos_sin_rol['rol']  # Remover rol
        
        form = CustomUserCreationForm(data=datos_sin_rol)
        
        self.assertFalse(form.is_valid())
        self.assertIn('rol', form.errors)

    def test_representacion_usuario(self):
        """Test: Representación string del usuario"""
        usuario = User.objects.create_user(
            username='usuario_string_test',
            password='Password123!'
        )
        
        self.assertEqual(str(usuario), 'usuario_string_test')

    def test_permisos_grupo(self):
        """Test: Verificación de permisos por grupo"""
        # Crear usuario y asignar a grupo
        usuario = User.objects.create_user(
            username='usuario_permisos',
            password='Password123!'
        )
        usuario.groups.add(self.grupo_admin)
        
        # Verificar que el usuario pertenece al grupo correcto
        self.assertTrue(usuario.groups.filter(name="Administrador").exists())