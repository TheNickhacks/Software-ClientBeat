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
        'rut',
        'rubro_google',
        'ciudad',
        'dueño',
        'cantidad_locales',
        'cantidad_miembros',
        'verificado',
        'estado',
        'fecha_creacion',
    ]
    list_filter = [
        'verificado',
        'estado',
        'ciudad',
        'rubro_google',
        'fecha_creacion',
    ]
    search_fields = [
        'nombre',
        'rut',
        'rubro_google',
        'email_contacto',
        'dueño__email',
    ]
    ordering = ['-fecha_creacion']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'fecha_verificacion']
    raw_id_fields = ['dueño']
    inlines = [MiembroEquipoInline, LocalInline]

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
        'estado',
        'fecha_creacion',
    ]
    list_filter = [
        'estado',
        'ciudad',
    ]
    search_fields = [
        'nombre',
        'direccion',
        'qr_token',
        'google_place_id',
        'negocio__nombre',
    ]
    readonly_fields = ['id', 'qr_token', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['negocio']
    ordering = ['-fecha_creacion']

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
