from django.utils.deprecation import MiddlewareMixin
from django.db.models import Q
from apps.businesses.models import Negocio, MiembroEquipo


class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.negocio = None
        request.negocios_qs = None
        request.rol_actual_negocio = None

        if not request.user or not request.user.is_authenticated:
            return

        if request.user.is_admin_soporte:
            request.negocios_qs = Negocio.objects.filter(
                estado=Negocio.EstadoChoices.ACTIVO
            )
            default_negocio = request.negocios_qs.first()
            if default_negocio:
                request.negocio = default_negocio
                request.rol_actual_negocio = 'ADMIN_SOPORTE'
            return

        from apps.businesses.models import MiembroEquipo

        if request.user.rol == 'DUENO':
            qs = Negocio.objects.filter(
                dueño_id=request.user.id,
                estado=Negocio.EstadoChoices.ACTIVO
            )
        else:
            ids_membresia = MiembroEquipo.objects.filter(
                usuario_id=request.user.id,
                estado=MiembroEquipo.EstadoChoices.ACTIVO
            ).values_list('negocio_id', flat=True)
            qs = Negocio.objects.filter(
                Q(id__in=ids_membresia) | Q(dueño_id=request.user.id),
                estado=Negocio.EstadoChoices.ACTIVO
            ).distinct()

        request.negocios_qs = qs
        default_negocio = qs.first()

        if default_negocio:
            request.negocio = default_negocio
            request.rol_actual_negocio = request.user.rol_en_negocio(default_negocio.id)
