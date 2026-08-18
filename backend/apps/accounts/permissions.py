from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


def rol_requerido(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/accounts/login/?next=' + request.path)
            if request.user.is_admin_soporte:
                return view_func(request, *args, **kwargs)
            if request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(
                '<h1>403 Prohibido</h1><p>No tienes el rol requerido para acceder a esta sección.</p>'
                '<a href="/dashboard/">Volver al panel</a>'
            )
        return _wrapped_view
    return decorator


def negocio_pertenece(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        if request.user.is_admin_soporte:
            return view_func(request, *args, **kwargs)
        negocio_id = kwargs.get('negocio_id') or request.GET.get('negocio_id') or getattr(request, 'negocio', None)
        if negocio_id and hasattr(negocio_id, 'id'):
            negocio_id = negocio_id.id
        if not negocio_id:
            return view_func(request, *args, **kwargs)
        if not request.user.pertenece_a_negocio(negocio_id):
            return HttpResponseForbidden(
                '<h1>403 Prohibido</h1><p>No tienes acceso a este negocio.</p>'
                '<a href="/dashboard/">Volver al panel</a>'
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permiso_gestion_cuenta(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        if request.user.is_admin_soporte:
            return view_func(request, *args, **kwargs)
        negocio_id = kwargs.get('negocio_id') or getattr(request, 'negocio', None)
        if negocio_id and hasattr(negocio_id, 'id'):
            negocio_id = negocio_id.id
        if not negocio_id:
            return HttpResponseForbidden(
                '<h1>403 Prohibido</h1><p>Contexto de negocio no definido.</p>'
            )
        if not request.user.puede_gestionar_cuenta(negocio_id):
            messages.error(request, 'Solo el dueño o soporte ClienBeat pueden modificar la configuración de la cuenta.')
            return redirect('/dashboard/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
