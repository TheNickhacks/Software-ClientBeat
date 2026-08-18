from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .admin_mixins import SuperUserOnlyAdminMixin


@admin.register(User)
class UserAdmin(SuperUserOnlyAdminMixin, BaseUserAdmin):
    list_display = [
        'email',
        'username',
        'first_name',
        'last_name',
        'get_rol_label',
        'es_mayor_18',
        'is_staff',
        'is_superuser',
        'is_active',
        'last_activity',
    ]
    list_filter = [
        'rol',
        'es_mayor_18',
        'is_staff',
        'is_superuser',
        'is_active',
        'fecha_creacion',
    ]
    search_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
        'telefono',
    ]
    ordering = ['-fecha_creacion']
    readonly_fields = [
        'id',
        'last_activity',
        'fecha_creacion',
        'fecha_actualizacion',
    ]
    fieldsets = (
        (None, {
            'fields': ('id', 'username', 'email', 'password')
        }),
        ('Información personal', {
            'fields': ('first_name', 'last_name', 'telefono', 'es_mayor_18', 'acepto_terminos')
        }),
        ('Permisos y Roles', {
            'fields': (
                'rol',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Fechas', {
            'fields': ('last_login', 'last_activity', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'rol'),
        }),
    )

    def get_rol_label(self, obj):
        return f'{obj.get_rol_display()}'
    get_rol_label.short_description = 'Rol'
    get_rol_label.admin_order_field = 'rol'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()
