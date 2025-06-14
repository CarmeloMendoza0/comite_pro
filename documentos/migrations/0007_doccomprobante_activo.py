# Generated by Django 5.1.2 on 2025-05-28 02:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0006_doccomprobante_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='doccomprobante',
            name='activo',
            field=models.BooleanField(default=True, help_text='Indica si el documento está activo en el sistema', verbose_name='Activo'),
        ),
    ]
