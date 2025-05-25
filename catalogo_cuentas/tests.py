from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import datetime

from .models import CatalogoCuentas, Cuenta
from empresa.models import Empresa


class CuentaContableTestCase(TestCase):
    """
    Pruebas para la creación y validación de Cuentas Contables
    Basado en Tabla 23: Datos Ingresados en la Prueba de Creación de Cuenta Contable
    """
    
    def setUp(self):
        """Configuración inicial para todas las pruebas"""
        # Crear empresa de prueba
        self.empresa = Empresa.objects.create(
            rtu="12345678901234",
            razon_social="Empresa de Prueba S.A.",
            giro="Comercio",
            direccion="Calle Principal 123",
            telefono="555-1234"
        )
        
        # Crear catálogo de cuentas de prueba
        self.catalogo = CatalogoCuentas.objects.create(
            empresa=self.empresa,
            nombre="Plan de Cuentas General",
            tipo="Activo"
        )
        
        # Crear cuenta padre para pruebas de jerarquía
        self.cuenta_padre = Cuenta.objects.create(
            catalogo=self.catalogo,
            nombre="Activos Corrientes",
            codigo="1000",
            saldo=Decimal('0.00'),
            nivel=1
        )

    def test_creacion_cuenta_contable_exitosa(self):
        """Test: Creación exitosa de cuenta contable con datos válidos"""
        cuenta = Cuenta.objects.create(
            nombre="Caja General",
            codigo="1001",
            saldo=Decimal('0.00'),
            nivel=2,
            catalogo=self.catalogo,
            parent=self.cuenta_padre
        )
        
        # Verificaciones
        self.assertEqual(cuenta.nombre, "Caja General")
        self.assertEqual(cuenta.codigo, "1001")
        self.assertEqual(cuenta.saldo, Decimal('0.00'))
        self.assertEqual(cuenta.nivel, 2)
        self.assertEqual(cuenta.catalogo, self.catalogo)
        self.assertEqual(cuenta.parent, self.cuenta_padre)
        self.assertIsNotNone(cuenta.fecha_creacion)

    def test_creacion_cuenta_sin_parent(self):
        """Test: Creación de cuenta principal sin cuenta padre"""
        cuenta = Cuenta.objects.create(
            nombre="Pasivos",
            codigo="2000",
            saldo=Decimal('0.00'),
            nivel=1,
            catalogo=self.catalogo,
            parent=None
        )
        
        self.assertIsNone(cuenta.parent)
        self.assertEqual(cuenta.nivel, 1)

    def test_codigo_cuenta_unico(self):
        """Test: Validación de código único de cuenta"""
        # Crear primera cuenta
        Cuenta.objects.create(
            nombre="Primera Cuenta",
            codigo="1002",
            saldo=Decimal('1000.00'),
            nivel=1,
            catalogo=self.catalogo
        )
        
        # Intentar crear segunda cuenta con mismo código
        with self.assertRaises(IntegrityError):
            Cuenta.objects.create(
                nombre="Segunda Cuenta",
                codigo="1002",  # Código duplicado
                saldo=Decimal('2000.00'),
                nivel=1,
                catalogo=self.catalogo
            )

    def test_validacion_catalogo_existente(self):
        """Test: Validación de catálogo existente"""
        cuenta = Cuenta(
            nombre="Cuenta de Prueba",
            codigo="1003",
            saldo=Decimal('0.00'),
            nivel=1,
            catalogo_id=9999  # ID de catálogo inexistente
        )
        
        with self.assertRaises(ValidationError):
            cuenta.clean()

    def test_saldo_inicial_correcto(self):
        """Test: Verificación de saldo inicial"""
        cuenta = Cuenta.objects.create(
            nombre="Banco Nacional",
            codigo="1004",
            saldo=Decimal('25000.50'),
            nivel=2,
            catalogo=self.catalogo,
            parent=self.cuenta_padre
        )
        
        self.assertEqual(cuenta.saldo, Decimal('25000.50'))

    def test_estructura_jerarquica(self):
        """Test: Verificación de estructura jerárquica de cuentas"""
        # Crear subcuenta
        subcuenta = Cuenta.objects.create(
            nombre="Efectivo en Caja",
            codigo="1001001",
            saldo=Decimal('1500.00'),
            nivel=3,
            catalogo=self.catalogo,
            parent=self.cuenta_padre
        )
        
        # Verificar relación padre-hijo
        self.assertEqual(subcuenta.parent, self.cuenta_padre)
        self.assertIn(subcuenta, self.cuenta_padre.subcuentas.all())

    def test_niveles_jerarquicos(self):
        """Test: Validación de niveles jerárquicos"""
        niveles_validos = [1, 2, 3, 4, 5]
        
        for nivel in niveles_validos:
            cuenta = Cuenta.objects.create(
                nombre=f"Cuenta Nivel {nivel}",
                codigo=f"100{nivel}",
                saldo=Decimal('0.00'),
                nivel=nivel,
                catalogo=self.catalogo
            )
            self.assertEqual(cuenta.nivel, nivel)

    def test_campos_obligatorios(self):
        """Test: Verificación de campos obligatorios"""
        # Intentar crear cuenta sin nombre
        with self.assertRaises(ValidationError):
            cuenta = Cuenta(
                codigo="1005",
                saldo=Decimal('0.00'),
                nivel=1,
                catalogo=self.catalogo
            )
            cuenta.full_clean()

    def test_representacion_string(self):
        """Test: Verificación del método __str__"""
        cuenta = Cuenta.objects.create(
            nombre="Inventarios",
            codigo="1300",
            saldo=Decimal('15000.00'),
            nivel=1,
            catalogo=self.catalogo
        )
        
        expected_str = "1300 - Inventarios"
        self.assertEqual(str(cuenta), expected_str)

    def test_relacion_con_catalogo(self):
        """Test: Verificación de relación con catálogo de cuentas"""
        cuenta = Cuenta.objects.create(
            nombre="Clientes",
            codigo="1200",
            saldo=Decimal('8000.00'),
            nivel=1,
            catalogo=self.catalogo
        )
        
        # Verificar que la cuenta está en el catálogo
        self.assertIn(cuenta, self.catalogo.cuentas.all())
        self.assertEqual(cuenta.catalogo.empresa, self.empresa)

    def test_actualizacion_saldo(self):
        """Test: Actualización de saldo de cuenta"""
        cuenta = Cuenta.objects.create(
            nombre="Proveedores",
            codigo="2100",
            saldo=Decimal('0.00'),
            nivel=1,
            catalogo=self.catalogo
        )
        
        # Actualizar saldo
        nuevo_saldo = Decimal('12500.75')
        cuenta.saldo = nuevo_saldo
        cuenta.save()
        
        # Verificar actualización
        cuenta.refresh_from_db()
        self.assertEqual(cuenta.saldo, nuevo_saldo)