"""Custom AdminSite que requiere is_superuser Django (no ADMIN_SOPORTE).

Cualquier usuario autenticado que sea ADMIN_SOPORTE pero NO superuser Django,
es redirigido al Panel Administrativo ClienBeat /admin-panel/ para que no entre
en la capa técnica de Django Admin.
"""
from django.contrib.admin import AdminSite as DjangoAdminSite
from django.contrib.admin.sites import site as default_site
from django.shortcuts import redirect
from django.urls import reverse


class ClientBeatSuperAdminSite(DjangoAdminSite):
    site_header = "🔒 SuperAdmin Técnico Client Beat (Solo SuperUser)"
    site_title = "SuperAdmin Client Beat"
    index_title = "Consola Técnica de Emergencia"
    site_url = "/admin-panel/"

    def has_permission(self, request):
        if not request.user.is_authenticated:
            return False
        if request.user.is_active and request.user.is_superuser:
            return True
        return False

    def admin_view(self, view, cacheable=False):
        """Wrapper global sobre TODAS las vistas del Admin Site (/admin/*).

        Cualquier usuario autenticado que NO sea superuser Django (is_superuser=True)
        es inmediatamente redirigido a /admin-panel/ (Panel ClienBeat no-técnico).
        Esto cubre: index, app_index, changelist, changeform, delete, history, etc.
        """
        original_view = super().admin_view(view, cacheable=cacheable)

        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and not request.user.is_superuser:
                return redirect('/admin-panel/')
            return original_view(request, *args, **kwargs)

        # Preserva metadata para evitar problemas con CSRF / debug
        try:
            from functools import wraps
            wrapper = wraps(original_view)(wrapper)
        except Exception:
            pass
        return wrapper

    def login(self, request, extra_context=None):
        resp = super().login(request, extra_context=extra_context)
        if request.method == "POST" and request.user.is_authenticated:
            if not request.user.is_superuser and getattr(request.user, 'is_admin_soporte', False):
                return redirect('/admin-panel/')
        return resp

    def index(self, request, extra_context=None):
        if request.user.is_authenticated and not request.user.is_superuser:
            return redirect('/admin-panel/')
        return super().index(request, extra_context=extra_context)


# Sobrescribe el sitio admin por defecto de Django (admin.site)
site = ClientBeatSuperAdminSite()
# Registrar en django.contrib.admin el site para que no use el default
# (los archivos admin.py deben registrar en este site, o se quedan en default)
default_site.__class__ = ClientBeatSuperAdminSite
default_site.site_header = site.site_header
default_site.site_title = site.site_title
default_site.index_title = site.index_title
default_site.site_url = site.site_url
