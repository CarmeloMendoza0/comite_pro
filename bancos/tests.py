from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, datetime

from .models import DocumentoBanco
from empresa.models import Empresa
from documentos.models import TipoDocumento
from terceros.models import Persona, Proveedor

class DocumentoBancarioTestCase(TestCase):
    """
    Pruebas para el registro de documentos bancarios
    Basado en Tabla 25: Datos Ingresados en la Prueba de Registro de Documento Bancario
    """
    def setUp(self):
        """Configuración inicial para todas las pruebas"""
        # Crear empresa de prueba
        self.empresa = Empresa.objects.create(
            rtu="12345678901234",
            razon_social="Banco Nacional S.A.",
            giro="Servicios Financieros",
            direccion="Avenida Principal 456",
            telefono="555-5678"
        )
        
        # Crear tipos de documento de prueba
        self.tipo_cheque = TipoDocumento.objects.create(
            nombre="Cheque",
            descripcion="Documento de pago bancario",
            tipo="Documento Bancario",
            codigo="CHQ"
        )
        
        self.tipo_deposito = TipoDocumento.objects.create(
            nombre="Depósito Bancario",
            descripcion="Comprobante de depósito",
            tipo="Documento Bancario",
            codigo="DEP"
        )
        
        # Crear entidad/persona de prueba
        self.entidad = Persona.objects.create(
            empresa=self.empresa,
            nombre="Juan Pérez",
            direccion="Calle Secundaria 789",
            telefono="555-9876",
            email="juan.perez@email.com",
            tipo=Persona.CLIENTE
        )
        
        # Crear proveedor de prueba
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre="Proveedor ABC S.A.",
            direccion="Zona Industrial 123",
            telefono="555-4321",
            email="contacto@proveedorabc.com"
        )

    def test_registro_documento_bancario_exitoso(self):
        """Test: Registro exitoso de documento bancario con datos válidos"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            entidad=self.entidad,
            numero_documento="CHQ-001-2024",
            fecha=date(2024, 5, 15),
            monto=Decimal('2500.00')
        )
        
        # Verificaciones
        self.assertEqual(documento.empresa, self.empresa)
        self.assertEqual(documento.tipo_documento, self.tipo_cheque)
        self.assertEqual(documento.entidad, self.entidad)
        self.assertEqual(documento.numero_documento, "CHQ-001-2024")
        self.assertEqual(documento.fecha, date(2024, 5, 15))
        self.assertEqual(documento.monto, Decimal('2500.00'))

    def test_registro_documento_con_proveedor(self):
        """Test: Registro de documento bancario asociado a proveedor"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_deposito,
            proveedor=self.proveedor,
            numero_documento="DEP-002-2024",
            fecha=date.today(),
            monto=Decimal('15000.50')
        )
        
        self.assertEqual(documento.proveedor, self.proveedor)
        self.assertIsNone(documento.entidad)  # No debe tener entidad cuando tiene proveedor

    def test_numero_documento_unico(self):
        """Test: Validación de número de documento único"""
        # Crear primer documento
        DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            entidad=self.entidad,
            numero_documento="DOC-UNICO-001",
            fecha=date.today(),
            monto=Decimal('1000.00')
        )
        
        # Intentar crear segundo documento con mismo número
        with self.assertRaises(IntegrityError):
            DocumentoBanco.objects.create(
                empresa=self.empresa,
                tipo_documento=self.tipo_deposito,
                proveedor=self.proveedor,
                numero_documento="DOC-UNICO-001",  # Número duplicado
                fecha=date.today(),
                monto=Decimal('2000.00')
            )

    def test_documento_sin_entidad_ni_proveedor(self):
        """Test: Documento bancario sin entidad ni proveedor (válido)"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_deposito,
            numero_documento="DEP-GENERAL-001",
            fecha=date.today(),
            monto=Decimal('5000.00')
        )
        
        self.assertIsNone(documento.entidad)
        self.assertIsNone(documento.proveedor)

    def test_monto_decimal_precision(self):
        """Test: Precisión decimal en montos"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            entidad=self.entidad,
            numero_documento="CHQ-DECIMAL-001",
            fecha=date.today(),
            monto=Decimal('1234.56')
        )
        
        self.assertEqual(documento.monto, Decimal('1234.56'))

    def test_diferentes_tipos_documento(self):
        """Test: Registro con diferentes tipos de documento"""
        tipos_documentos = [
            (self.tipo_cheque, "CHQ-TIPO-001"),
            (self.tipo_deposito, "DEP-TIPO-001")
        ]
        
        for tipo_doc, numero in tipos_documentos:
            documento = DocumentoBanco.objects.create(
                empresa=self.empresa,
                tipo_documento=tipo_doc,
                entidad=self.entidad,
                numero_documento=numero,
                fecha=date.today(),
                monto=Decimal('1000.00')
            )
            
            self.assertEqual(documento.tipo_documento, tipo_doc)

    def test_relacion_con_empresa(self):
        """Test: Verificación de relación con empresa"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            numero_documento="CHQ-EMPRESA-001",
            fecha=date.today(),
            monto=Decimal('3000.00')
        )
        
        # Verificar que el documento está en la empresa
        self.assertIn(documento, self.empresa.documentos_banco.all())

    def test_campos_obligatorios(self):
        """Test: Verificación de campos obligatorios"""
        # Intentar crear documento sin empresa (campo obligatorio)
        with self.assertRaises(IntegrityError):
            DocumentoBanco.objects.create(
                tipo_documento=self.tipo_cheque,
                numero_documento="CHQ-SIN-EMPRESA",
                fecha=date.today(),
                monto=Decimal('1000.00')
            )

    def test_representacion_string(self):
        """Test: Verificación del método __str__"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            entidad=self.entidad,
            numero_documento="CHQ-STRING-001",
            fecha=date.today(),
            monto=Decimal('7500.25')
        )
        
        expected_str = "CHQ-STRING-001 - Cheque - 7500.25"
        self.assertEqual(str(documento), expected_str)

    def test_fechas_validas(self):
        """Test: Validación de fechas válidas"""
        fechas_test = [
            date.today(),
            date(2024, 1, 1),
            date(2024, 12, 31)
        ]
        
        for i, fecha in enumerate(fechas_test):
            documento = DocumentoBanco.objects.create(
                empresa=self.empresa,
                tipo_documento=self.tipo_deposito,
                numero_documento=f"DEP-FECHA-{i+1:03d}",
                fecha=fecha,
                monto=Decimal('1000.00')
            )
            
            self.assertEqual(documento.fecha, fecha)

    def test_monto_cero_positivo(self):
        """Test: Validación de montos válidos (positivos y cero)"""
        montos_validos = [
            Decimal('0.00'),
            Decimal('0.01'),
            Decimal('999999.99'),
            Decimal('1000000.00')
        ]
        
        for i, monto in enumerate(montos_validos):
            documento = DocumentoBanco.objects.create(
                empresa=self.empresa,
                tipo_documento=self.tipo_cheque,
                numero_documento=f"CHQ-MONTO-{i+1:03d}",
                fecha=date.today(),
                monto=monto
            )
            
            self.assertEqual(documento.monto, monto)

    def test_relaciones_cascade_restrict(self):
        """Test: Verificación de comportamiento de eliminación en cascada"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            entidad=self.entidad,
            numero_documento="CHQ-CASCADE-001",
            fecha=date.today(),
            monto=Decimal('5000.00')
        )
        
        # Al eliminar la empresa, debe eliminarse el documento (CASCADE)
        documento_id = documento.id
        self.empresa.delete()
        
        with self.assertRaises(DocumentoBanco.DoesNotExist):
            DocumentoBanco.objects.get(id=documento_id)

    def test_entidad_set_null(self):
        """Test: Verificación de SET_NULL al eliminar entidad"""
        documento = DocumentoBanco.objects.create(
            empresa=self.empresa,
            tipo_documento=self.tipo_cheque,
            entidad=self.entidad,
            numero_documento="CHQ-SETNULL-001",
            fecha=date.today(),
            monto=Decimal('2000.00')
        )
        
        # Al eliminar la entidad, el campo debe quedar null
        self.entidad.delete()
        documento.refresh_from_db()
        
        self.assertIsNone(documento.entidad)

    def test_multiples_documentos_misma_entidad(self):
        """Test: Una entidad puede tener múltiples documentos bancarios"""
        documentos = []
        for i in range(3):
            doc = DocumentoBanco.objects.create(
                empresa=self.empresa,
                tipo_documento=self.tipo_cheque,
                entidad=self.entidad,
                numero_documento=f"CHQ-MULTI-{i+1:03d}",
                fecha=date.today(),
                monto=Decimal(f'{(i+1)*1000}.00')
            )
            documentos.append(doc)
        
        # Verificar que la entidad tiene todos los documentos
        documentos_entidad = self.entidad.documentos_banco.all()
        self.assertEqual(documentos_entidad.count(), 3)
        
        for doc in documentos:
            self.assertIn(doc, documentos_entidad)