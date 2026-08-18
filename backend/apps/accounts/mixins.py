from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin


class RolRequeridoMixin(AccessMixin):
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_admin_soporte:
            return super().dispatch(request, *args, **kwargs)
        if request.user.rol in self.roles_permitidos:
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class NegocioPerteneceMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        if request.user.is_admin_soporte:
            return super().dispatch(request, *args, **kwargs)
        negocio_id = kwargs.get('negocio_id') or getattr(request, 'negocio', None)
        if negocio_id and hasattr(negocio_id, 'id'):
            negocio_id = negocio_id.id
        if not negocio_id:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.pertenece_a_negocio(negocio_id):
            return HttpResponseForbidden(
                '<h1>403 Prohibido</h1><p>No tienes acceso a este negocio.</p>'
                '<a href="/dashboard/">Volver al panel</a>'
            )
        return super().dispatch(request, *args, **kwargs)


class PermisoGestionCuentaMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        if request.user.is_admin_soporte:
            return super().dispatch(request, *args, **kwargs)
        negocio_id = kwargs.get('negocio_id') or getattr(request, 'negocio', None)
        if negocio_id and hasattr(negocio_id, 'id'):
            negocio_id = negocio_id.id
        if not negocio_id:
            return HttpResponseForbidden('<h1>403 Prohibido</h1><p>Contexto de negocio no definido.</p>')
        if not request.user.puede_gestionar_cuenta(negocio_id):
            messages.error(request, 'Solo el dueño o soporte ClienBeat pueden modificar la configuración de la cuenta.')
            return redirect('/dashboard/')
        return super().dispatch(request, *args, **kwargs)
