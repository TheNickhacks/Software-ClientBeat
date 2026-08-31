from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Sincroniza las reseñas Google y el benchmark de TODOS los locales ACTIVOS. '
        'Pensado para ejecutarse como tarea Celery Beat diaria. '
        'Ej: python -X utf8 manage.py sincronizar_google_places'
    )

    def handle(self, *args, **options):
        from apps.reputation.management.commands.sincronizar_google_local import Command as LocalCommand
        cmd = LocalCommand()
        cmd.stdout = self.stdout
        cmd.stderr = self.stderr
        return cmd.handle(todos=True, local_id=None)
