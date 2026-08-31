from django.contrib import admin
from apps.accounts.admin_mixins import SuperUserOnlyAdminMixin
from .models import AuditoriaAdmin, AccionAuditoriaChoices, ModuloAuditoriaChoices


@admin.register(AuditoriaAdmin)
class AuditoriaAdminAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'fecha_hora',
        'usuario_email',
        'get_accion_display',
        'get_modulo_display',
        'entidad_tipo',
        'entidad_descripcion',
        'ip_origen',
    ]
    list_filter = [
        'accion',
        'modulo',
        ('usuario', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'usuario_email',
        'entidad_tipo',
        'entidad_id',
        'entidad_descripcion',
        'notas_internas',
        'ip_origen',
    ]
    readonly_fields = [
        'id',
        'fecha_hora',
        'usuario',
        'usuario_email',
        'accion',
        'modulo',
        'entidad_tipo',
        'entidad_id',
        'entidad_descripcion',
        'datos_antes',
        'datos_despues',
        'notas_internas',
        'ip_origen',
        'user_agent',
    ]
    date_hierarchy = 'fecha_hora'
    fieldsets = (
        (None, {
            'fields': (
                'id', 'fecha_hora',
                ('usuario', 'usuario_email', 'ip_origen'),
                ('accion', 'modulo'),
                ('entidad_tipo', 'entidad_id'),
                'entidad_descripcion',
            ),
        }),
        ('Detalle de la acción', {
            'fields': (
                'datos_antes', 'datos_despues', 'notas_internas', 'user_agent',
            ),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
