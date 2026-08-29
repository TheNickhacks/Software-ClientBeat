from django.contrib import admin
from apps.accounts.admin_mixins import SuperUserOnlyAdminMixin
from .models import (
    Negocio,
    MiembroEquipo,
    Local,
    Competidor,
    SnapshotReputacion,
)


class MiembroEquipoInline(SuperUserOnlyAdminMixin, admin.TabularInline):
    model = MiembroEquipo
    extra = 0
    raw_id_fields = ['usuario', 'invitado_por']
    fields = ['usuario', 'rol', 'estado', 'permisos', 'fecha_invitacion', 'fecha_aceptacion', 'invitado_por']
    readonly_fields = ['fecha_invitacion']


class LocalInline(SuperUserOnlyAdminMixin, admin.TabularInline):
    model = Local
    extra = 0
    fields = ['nombre', 'ciudad', 'qr_token', 'estado']
    readonly_fields = ['qr_token']


@admin.register(Negocio)
class NegocioAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'razon_social',
        'rut',
        'rango_empleados',
        'rubro_google',
        'ciudad',
        'dueño',
        'cantidad_locales',
        'cantidad_miembros',
        'verificado',
        'acepto_politica',
        'estado',
        'fecha_creacion',
    ]
    list_filter = [
        'verificado',
        'estado',
        'ciudad',
        'rubro_google',
        'rango_empleados',
        'fecha_creacion',
    ]
    search_fields = [
        'nombre',
        'razon_social',
        'rut',
        'rubro_google',
        'email_contacto',
        'dueño__email',
    ]
    ordering = ['-fecha_creacion']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'fecha_verificacion']
    raw_id_fields = ['dueño']
    inlines = [MiembroEquipoInline, LocalInline]

    def acepto_politica(self, obj):
        return obj.acepto_politica_datos.strftime('%d-%m-%Y') if obj.acepto_politica_datos else '—'
    acepto_politica.short_description = 'LOPD'

    def cantidad_locales(self, obj):
        return obj.locales.count()
    cantidad_locales.short_description = 'Locales'

    def cantidad_miembros(self, obj):
        return obj.miembros_equipo.count()
    cantidad_miembros.short_description = 'Equipo'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


@admin.register(MiembroEquipo)
class MiembroEquipoAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'usuario',
        'negocio',
        'rol',
        'permisos_por_rol_display',
        'permisos_custom_count',
        'estado',
        'fecha_invitacion',
        'fecha_aceptacion',
        'invitado_por',
    ]
    list_filter = [
        'rol',
        'estado',
        'fecha_invitacion',
    ]
    search_fields = [
        'usuario__email',
        'usuario__first_name',
        'usuario__last_name',
        'negocio__nombre',
    ]
    raw_id_fields = ['negocio', 'usuario', 'invitado_por']
    readonly_fields = ['id', 'fecha_invitacion']
    ordering = ['-fecha_invitacion']

    def permisos_por_rol_display(self, obj):
        defaults = obj.permisos_por_rol
        if not defaults:
            return '—'
        return ', '.join(defaults) if isinstance(defaults, list) else str(defaults)
    permisos_por_rol_display.short_description = 'Permisos (defaults rol)'
    permisos_por_rol_display.admin_order_field = 'rol'

    def permisos_custom_count(self, obj):
        if not obj.permisos:
            return 0
        return len(obj.permisos) if isinstance(obj.permisos, list) else 'ERR'
    permisos_custom_count.short_description = 'Permisos (custom)'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


@admin.register(Local)
class LocalAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'negocio',
        'ciudad',
        'qr_token',
        'qr_colores',
        'qr_config_resumen',
        'estado',
        'fecha_creacion',
    ]
    list_filter = [
        'estado',
        'ciudad',
        'qr_error_level',
        'qr_mostrar_logo',
    ]
    search_fields = [
        'nombre',
        'direccion',
        'qr_token',
        'google_place_id',
        'negocio__nombre',
        'qr_texto_corto',
        'qr_encabezado',
    ]
    readonly_fields = ['id', 'qr_token', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['negocio', 'comuna']
    ordering = ['-fecha_creacion']
    fieldsets = (
        (None, {
            'fields': ('id', 'negocio', 'nombre', 'estado', 'fecha_creacion', 'fecha_actualizacion')
        }),
        ('Ubicación y Google', {
            'fields': ('direccion', 'ciudad', 'comuna', 'latitud', 'longitud', 'google_place_id', 'horario'),
            'classes': ('collapse',),
        }),
        ('QR Personalización ClientBeat (Plan2/Plan3)', {
            'fields': (
                'qr_token',
                ('qr_logo', 'qr_mostrar_logo'),
                ('qr_color_primario', 'qr_color_secundario', 'qr_color_fondo'),
                ('qr_encabezado', 'qr_texto_corto'),
                ('qr_tamano_pixels', 'qr_error_level', 'qr_estilo_borde'),
            ),
            'description': 'Campos de personalización del código QR de experiencia cliente (disponible Planes 2 y 3). Defaults colores indigo/morado ClientBeat, error H 30% recomendado con logo centro.',
        }),
    )

    def qr_colores(self, obj):
        return f'{obj.qr_color_primario or "-"} / {obj.qr_color_secundario or "-"}'
    qr_colores.short_description = 'QR Colores'

    def qr_config_resumen(self, obj):
        config = []
        if obj.qr_logo:
            config.append('LOGO')
        if obj.qr_mostrar_logo:
            config.append('Mostrar Logo')
        if obj.qr_estilo_borde:
            config.append('Glass borde')
        config.append(f'T{obj.qr_tamano_pixels}')
        config.append(f'E{obj.qr_error_level}')
        return ' | '.join(config)
    qr_config_resumen.short_description = 'QR Config'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


@admin.register(Competidor)
class CompetidorAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'local',
        'rubro',
        'distancia_km',
        'calificacion_global',
        'numero_opiniones',
        'estado',
    ]
    list_filter = [
        'estado',
        'rubro',
    ]
    search_fields = [
        'nombre',
        'direccion',
        'google_place_id',
    ]
    readonly_fields = ['id', 'ultima_actualizacion', 'fecha_creacion']
    raw_id_fields = ['local']
    ordering = ['distancia_km']


@admin.register(SnapshotReputacion)
class SnapshotReputacionAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'local',
        'competidor',
        'fecha_captura',
        'calificacion',
        'opiniones',
        'rank',
    ]
    list_filter = [
        'fecha_captura',
    ]
    search_fields = [
        'local__nombre',
        'competidor__nombre',
    ]
    readonly_fields = ['id', 'fecha_captura']
    raw_id_fields = ['local', 'competidor']
    ordering = ['-fecha_captura']
