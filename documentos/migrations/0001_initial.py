# Generated by Django 5.1.2 on 2024-10-17 05:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('empresa', '0004_alter_empresa_razon_social'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, verbose_name='Nombre')),
                ('descripcion', models.CharField(blank=True, max_length=255, null=True, verbose_name='Descripción')),
                ('tipo', models.CharField(choices=[('Comprobante', 'Comprobante'), ('Póliza', 'Póliza'), ('Documento Bancario', 'Documento Bancario')], max_length=20, verbose_name='Tipo')),
                ('codigo', models.CharField(max_length=20, unique=True, verbose_name='Código')),
            ],
        ),
        migrations.CreateModel(
            name='DocComprobante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(blank=True, max_length=255, null=True, verbose_name='Descripción')),
                ('numero_documento', models.CharField(max_length=50, verbose_name='Documento')),
                ('serie_documento', models.CharField(blank=True, max_length=50, null=True, verbose_name='Serie')),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('monto_total', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Monto')),
                ('estado', models.CharField(choices=[('Emitido', 'Emitido'), ('Pagado', 'Pagado'), ('Anulado', 'Anulado')], default='Emitido', max_length=10)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='empresa.empresa')),
                ('tipo_documento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='documentos.tipodocumento')),
            ],
        ),
    ]
