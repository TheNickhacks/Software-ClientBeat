from django.utils.deprecation import MiddlewareMixin
from django.db.models import Q
from apps.businesses.models import Negocio, MiembroEquipo


class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.negocio = None
        request.negocios_qs = None
        request.rol_actual_negocio = None

        # Omitir consultas a la BD en archivos estáticos/media/favicon
        path = request.path_info
        if path.startswith(('/static/', '/media/', '/favicon.ico')):
            return

        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return

        if request.user.is_admin_soporte:
            request.negocios_qs = Negocio.objects.select_related('dueño', 'rubro', 'comuna').filter(
                estado=Negocio.EstadoChoices.ACTIVO
            )
            default_negocio = request.negocios_qs.first()
            if default_negocio:
                request.negocio = default_negocio
                request.rol_actual_negocio = 'ADMIN_SOPORTE'
            return

        if request.user.rol == 'DUENO':
            qs = Negocio.objects.select_related('dueño', 'rubro', 'comuna').filter(
                dueño_id=request.user.id,
                estado=Negocio.EstadoChoices.ACTIVO
            )
        else:
            ids_membresia = MiembroEquipo.objects.filter(
                usuario_id=request.user.id,
                estado=MiembroEquipo.EstadoChoices.ACTIVO
            ).values_list('negocio_id', flat=True)
            qs = Negocio.objects.select_related('dueño', 'rubro', 'comuna').filter(
                Q(id__in=ids_membresia) | Q(dueño_id=request.user.id),
                estado=Negocio.EstadoChoices.ACTIVO
            ).distinct()

        request.negocios_qs = qs
        default_negocio = qs.first()

        if default_negocio:
            request.negocio = default_negocio
            # Optimización: si el usuario es el dueño directo, evitar consulta extra
            if default_negocio.dueño_id == request.user.id:
                request.rol_actual_negocio = 'DUENO'
            else:
                request.rol_actual_negocio = request.user.rol_en_negocio(default_negocio.id)

