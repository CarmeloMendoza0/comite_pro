# Generated by Django 5.1.2 on 2024-10-29 00:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bancos', '0003_alter_documentobanco_tipo_documento_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentobanco',
            name='cuenta',
        ),
    ]
