from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.billing.models import Suscripcion, EstadoSuscripcionChoices
from apps.billing.views import enviar_email_evento_facturacion


def ejecutar_barrido_ciclos_vencidos(stdout=None) -> dict:
    """
    Revisa todas las suscripciones activas, vencidas o en período de gracia:
      1. Si venció hoy y está dentro de los 3 días de gracia -> pasa a EN_GRACIA y envía alerta inicial.
      2. Si está en EN_GRACIA y le queda 1 día restante -> envía recordatorio urgente ('ultima_advertencia').
      3. Si superó los 3 días de gracia -> pasa a SUSPENDIDA (activa Hard Paywall) y envía correo de suspensión.
    """
    ahora = timezone.now()
    stats = {
        'pasadas_a_gracia': 0,
        'ultimas_advertencias': 0,
        'suspendidas': 0,
    }

    qs = Suscripcion.objects.select_related('negocio', 'negocio__dueño', 'plan').filter(
        estado__in=[
            EstadoSuscripcionChoices.ACTIVA,
            EstadoSuscripcionChoices.VENCIDA,
            EstadoSuscripcionChoices.EN_GRACIA,
        ],
        fecha_vencimiento__lt=ahora,
    )

    for sus in qs:
        dias_gracia = sus.dias_gracia or getattr(settings, 'FLOW_DIAS_GRACIA_IMPAGO', 3)
        limite_gracia = sus.fecha_vencimiento + timedelta(days=dias_gracia)

        if ahora > limite_gracia:
            # Superó los días de gracia -> Suspender acceso definitivamente
            sus.estado = EstadoSuscripcionChoices.SUSPENDIDA
            sus.save(update_fields=['estado'])
            enviar_email_evento_facturacion(sus, 'suspension')
            stats['suspendidas'] += 1
            if stdout:
                stdout.write(f"[SUSPENDIDA] Negocio '{sus.negocio.nombre}' superó los {dias_gracia} días de gracia.")
        else:
            # Aún está dentro de los 3 días de gracia
            cambio_a_gracia = False
            if sus.estado != EstadoSuscripcionChoices.EN_GRACIA:
                sus.estado = EstadoSuscripcionChoices.EN_GRACIA
                sus.save(update_fields=['estado'])
                cambio_a_gracia = True
                stats['pasadas_a_gracia'] += 1

            dias_rest = sus.dias_restantes_gracia()
            if dias_rest == 1:
                enviar_email_evento_facturacion(sus, 'ultima_advertencia')
                stats['ultimas_advertencias'] += 1
                if stdout:
                    stdout.write(f"[ULTIMA ADVERTENCIA - 1 DIA] Negocio '{sus.negocio.nombre}'.")
            elif cambio_a_gracia:
                enviar_email_evento_facturacion(sus, 'gracia')
                if stdout:
                    stdout.write(f"[EN GRACIA - {dias_rest} DIAS] Negocio '{sus.negocio.nombre}'.")

    return stats


class Command(BaseCommand):
    help = "Procesa diariamente los períodos de gracia (3 días), recordatorios Dunning y suspensiones por impago en Flow."

    def handle(self, *args, **options):
        self.stdout.write("=== Iniciando barrido diario de suscripciones y períodos de gracia Flow ===")
        stats = ejecutar_barrido_ciclos_vencidos(stdout=self.stdout)
        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] Barrido completado: {stats['pasadas_a_gracia']} en gracia | "
                f"{stats['ultimas_advertencias']} últimas advertencias | "
                f"{stats['suspendidas']} cuentas suspendidas."
            )
        )

