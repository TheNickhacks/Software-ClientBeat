import logging
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from apps.billing.models import Suscripcion, EstadoSuscripcionChoices

logger = logging.getLogger('clientbeat')


class SubscriptionRequiredMiddleware(MiddlewareMixin):
    """
    Middleware de control de acceso por Suscripción (Hard Paywall).
    Verifica que el negocio activo del usuario cuente con una suscripción válida y pagada.
    Si la suscripción está suspendida, vencida (fuera del período de gracia) o cancelada,
    bloquea el acceso a las funciones del Dashboard y redirige a la pantalla de regularización.
    """

    EXEMPT_URL_PREFIXES = (
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/',
        '/admin-soporte/',
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/password_reset/',
        '/accounts/registro/',
        '/accounts/onboarding/',
        '/billing/flow/',
        '/billing/bloqueado/',
        '/encuestas/publica/',
        '/encuestas/respondida/',
        '/e/',
        '/qr/',
        '/api/encuestas/',
        '/terminos-y-condiciones/',
        '/politica-de-privacidad/',
    )

    EXEMPT_EXACT_URLS = (
        '/',
        '/accounts/logout/',
    )

    def process_request(self, request):
        path = request.path_info

        # 1. Omitir URLs públicas, de autenticación, onboarding y webhooks
        if path in self.EXEMPT_EXACT_URLS:
            return None
        for prefix in self.EXEMPT_URL_PREFIXES:
            if path.startswith(prefix):
                return None

        # 2. Solo evaluar usuarios autenticados
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return None

        # 3. Personal de soporte y superusuarios tienen pase libre
        if getattr(request.user, 'is_admin_soporte', False) or getattr(request.user, 'is_staff', False):
            return None

        # 4. Obtener negocio activo (inyectado previamente por TenantMiddleware)
        negocio = getattr(request, 'negocio', None)
        if not negocio:
            # Si aún no tiene negocio creado, el flujo de onboarding se encarga
            return None

        # 5. Obtener suscripción del negocio
        suscripcion = Suscripcion.objects.select_related('plan').filter(negocio=negocio).first()
        request.suscripcion = suscripcion

        # Si no existe suscripción, redirigir al paso 3 de onboarding
        if not suscripcion:
            return redirect(f"{reverse('accounts:onboarding')}?paso=3")

        # 6. Evaluar bloqueo estricto (Hard Paywall)
        if suscripcion.esta_bloqueada():
            # Permitir acceso al perfil para ver datos propios, pero bloqueando el resto
            if path.startswith('/accounts/perfil/'):
                return None
            return redirect('billing:bloqueado')

        # 7. Si está en período de gracia (dentro de los 3 días tras fallo de cobro)
        if suscripcion.en_periodo_gracia():
            request.en_periodo_gracia = True
            request.dias_restantes_gracia = suscripcion.dias_restantes_gracia()

        return None
