from django.contrib import admin
from .models import PlantillaEncuesta, RespuestaEncuesta
from apps.accounts.admin_mixins import SuperUserOnlyAdminMixin


@admin.register(PlantillaEncuesta)
class PlantillaEncuestaAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['nombre', 'orden', 'es_default', 'activa', 'activar_nps', 'activar_csat', 'fecha_creacion']
    list_filter = ['es_default', 'activa', 'activar_nps', 'activar_csat']
    search_fields = ['nombre', 'nombre_mostrar', 'descripcion']
    filter_horizontal = ['rubros']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    fieldsets = [
        ('Datos básicos', {
            'fields': ['nombre', 'nombre_mostrar', 'descripcion', 'orden', 'es_default', 'activa'],
        }),
        ('Preguntas NPS + CSAT + Comentario', {
            'fields': ['activar_nps', 'titulo_nps', 'activar_csat', 'titulo_csat', 'activar_comentario', 'titulo_comentario', 'comentario_requerido', 'preguntas_extra'],
        }),
        ('Visibilidad por rubros', {
            'fields': ['rubros'],
            'description': 'Si está vacío, la plantilla se aplica a TODOS los rubros (recomendado para default).',
        }),
        ('Fechas', {
            'classes': ('collapse',),
            'fields': ['fecha_creacion', 'fecha_actualizacion'],
        }),
    ]


@admin.register(RespuestaEncuesta)
class RespuestaEncuestaAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['fecha_respuesta', 'local', 'nps_puntaje', 'nps_categoria_admin', 'csat_emocion', 'origen', 'es_anonima']
    list_filter = ['origen', 'csat_emocion', 'es_anonima', 'plantilla']
    search_fields = ['local__nombre', 'comentario', 'email_opcional']
    readonly_fields = ['fecha_respuesta', 'local', 'plantilla']
    date_hierarchy = 'fecha_respuesta'

    def nps_categoria_admin(self, obj):
        return obj.nps_categoria()
    nps_categoria_admin.short_description = 'Categoría NPS'
    nps_categoria_admin.admin_order_field = 'nps_puntaje'
