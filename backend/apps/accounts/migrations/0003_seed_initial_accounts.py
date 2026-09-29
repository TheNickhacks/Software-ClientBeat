from django.db import migrations


def create_seed_accounts(apps, schema_editor):
    """
    Data migration que inserta/asegura las cuentas semillas en la base de datos
    durante la ejecución de 'python manage.py migrate' en cualquier entorno (dev, staging, prod).
    """
    from django.core.management import call_command
    try:
        call_command('seed_demo')
    except Exception as e:
        print(f"[Migration Warning] Could not run seed_demo automatically: {e}")


def reverse_seed_accounts(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_rol'),
    ]

    operations = [
        migrations.RunPython(create_seed_accounts, reverse_code=reverse_seed_accounts),
    ]
