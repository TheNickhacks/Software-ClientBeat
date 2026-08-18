"""Mixin para Django Admin: solo SuperUser Django (is_superuser=True) tiene acceso.

Aplícalo a TODOS los ModelAdmin para que el ADMIN_SOPORTE normal NO pueda entrar
a /admin/ (la capa técnica). Ellos deben usar /admin-panel/ (Panel Admin ClienBeat no-técnico).
"""


class SuperUserOnlyAdminMixin:
    """Heredar primero, luego de admin.ModelAdmin/UserAdmin/etc."""

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return bool(request.user.is_active and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return bool(request.user.is_active and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return bool(request.user.is_active and request.user.is_superuser)
