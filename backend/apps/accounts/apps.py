from django.apps import AppConfig
from django.db.models.signals import post_migrate


def auto_ensure_seed_accounts(sender, **kwargs):
    """
    Verifica post-migración que las cuentas semillas principales existan.
    Si falta alguna de las cuentas base, ejecuta 'seed_demo' de forma idempotente.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        super_exists = User.objects.filter(email='super@clientbeat.cl').exists()
        admin_exists = User.objects.filter(email='admin@clientbeat.cl').exists()
        dueno_exists = User.objects.filter(email='dueno@negociodemo.cl').exists()
        if not (super_exists and admin_exists and dueno_exists):
            from django.core.management import call_command
            call_command('seed_demo')
    except Exception as e:
        # Evita bloquear migraciones si hay algún error de lectura en base de datos en transición
        pass


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Cuentas de Usuario'

    def ready(self):
        post_migrate.connect(auto_ensure_seed_accounts, sender=self)
