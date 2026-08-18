from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages


class AdminSoporteRequiredMixin(AccessMixin):
    """Mixin para vistas del Panel Admin ClienBeat.
    Requiere que el usuario esté autenticado y sea ADMIN_SOPORTE
    o SUPERUSER Django (ambos tienen acceso al panel no-técnico).
    SuperUser Django SI tiene acceso al panel de soporte (por conveniencia).
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if request.user.is_active and (
            getattr(request.user, 'is_admin_soporte', False) or request.user.is_superuser
        ):
            return super().dispatch(request, *args, **kwargs)
        messages.error(
            request,
            'No tienes permiso para acceder al Panel Administrativo de Client Beat.'
        )
        return redirect('/dashboard/')


class SuperUserRequiredMixin(AccessMixin):
    """Mixin para vistas QUE SOLO VE el SuperUser Django (no el ADMIN_SOPORTE ni el dueño).
    Úsalo para vistas técnicas: salud de DB, migraciones, logs de celery, etc.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if request.user.is_active and request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        messages.error(
            request,
            'Esta sección es solo para SuperUser. Pide acceso al administrador técnico si lo necesitas.'
        )
        return redirect('/admin-panel/')
