import os
import sys
import uuid as _uuid
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.businesses.models import Local


class Command(BaseCommand):
    help = (
        'Sincroniza las reseñas Google de UN solo local por ID (UUID). '
        'Usa USE_MOCK_GOOGLE_PLACES=True por defecto si no hay GOOGLE_PLACES_API_KEY. '
        'Ej: python -X utf8 manage.py sincronizar_google_local <id_local>'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'local_id',
            type=str,
            nargs='?',
            help='UUID del Local a sincronizar',
        )
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Ignora local_id y sincroniza TODOS los locales ACTIVOS (equivalente a sincronizar_google_places).',
        )

    def print_resultado(self, resultado):
        ok = '✅' if resultado.rating_sync_ok and not resultado.error else '⚠️'
        self.stdout.write(
            f'{ok} Local {resultado.local_id[:8]}… · {resultado.nombre}\n'
            f'    · place_id usado: {resultado.place_id_usado or "N/A"}\n'
            f'    · Nuevas: {resultado.nuevas_resenas} · Actualizadas: {resultado.actualizadas_resenas} · Sin cambios: {resultado.skip_duplicadas}\n'
            f'    · Rating sync: {"OK" if resultado.rating_sync_ok else "SIN DATOS"}'
            + (f'\n    · Error: {resultado.error}' if resultado.error else '')
        )

    def handle(self, *args, **options):
        try:
            from apps.reputation.services import GooglePlacesSyncService
        except Exception as e:
            raise CommandError(f'No se pudo cargar GooglePlacesSyncService: {e}') from e

        todos = bool(options.get('todos'))
        local_id_arg = options.get('local_id')

        if not todos and not local_id_arg:
            raise CommandError('Especifica <local_id> (UUID) o usa --todos para sincronizar todo.')

        service = GooglePlacesSyncService()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'[Sincronización Google Places] MODO={"MOCK" if __import__("django.conf", fromlist=["settings"]).settings.USE_MOCK_GOOGLE_PLACES else "LIVE API"} · hora: {timezone.now():%d/%m/%Y %H:%M:%S}'
        ))

        if todos:
            locales_qs = Local.objects.filter(estado=Local.EstadoChoices.ACTIVO)
            total = locales_qs.count()
            self.stdout.write(f'Sincronizando TODOS los locales activos ({total})...')
            resultados = service.sincronizar_todos(locales_qs)
        else:
            try:
                _uuid.UUID(str(local_id_arg))
            except Exception as e:
                raise CommandError(f'<local_id> debe ser un UUID válido. Recibido "{local_id_arg}": {e}') from e
            try:
                local = Local.objects.select_related('negocio', 'negocio__rubro', 'comuna').get(id=local_id_arg)
            except Local.DoesNotExist:
                raise CommandError(f'No existe Local con id={local_id_arg}')
            self.stdout.write(f'Sincronizando Local → {local.nombre} (id={local.id})...')
            resultados = [service.sincronizar_local(local)]
            total = 1

        ok = 0
        with_errors = 0
        nuevas_total = 0
        actualizadas_total = 0
        skip_total = 0
        for r in resultados:
            self.print_resultado(r)
            if r.rating_sync_ok and not r.error:
                ok += 1
            else:
                with_errors += 1
            nuevas_total += r.nuevas_resenas
            actualizadas_total += r.actualizadas_resenas
            skip_total += r.skip_duplicadas

        self.stdout.write(self.style.SUCCESS(
            f'\n📊 Resumen sincronización Google Places:\n'
            f'   · Locales procesados : {total}\n'
            f'   · OK                 : {ok}\n'
            f'   · Con errores        : {with_errors}\n'
            f'   · Reseñas nuevas     : {nuevas_total}\n'
            f'   · Reseñas actualiz.  : {actualizadas_total}\n'
            f'   · Sin cambios (dup.) : {skip_total}'
        ))

        if with_errors > 0 and ok == 0:
            sys.exit(2)
