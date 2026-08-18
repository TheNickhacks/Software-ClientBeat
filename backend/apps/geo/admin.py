from django.contrib import admin
from apps.accounts.admin_mixins import SuperUserOnlyAdminMixin
from .models import Region, Provincia, Comuna, Rubro


class ProvinciaInline(SuperUserOnlyAdminMixin, admin.TabularInline):
    model = Provincia
    extra = 0
    fields = ['nombre', 'orden']
    show_change_link = True


class ComunaInline(SuperUserOnlyAdminMixin, admin.TabularInline):
    model = Comuna
    extra = 0
    fields = ['nombre', 'orden']


@admin.register(Region)
class RegionAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'codigo_romano',
        'nombre',
        'orden',
        'cantidad_provincias',
        'cantidad_comunas',
        'activo',
    ]
    list_filter = ['activo']
    search_fields = ['nombre', 'codigo_romano']
    list_editable = ['orden', 'activo']
    ordering = ['orden', 'codigo_romano']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    inlines = [ProvinciaInline]

    def cantidad_provincias(self, obj):
        return obj.provincias.count()
    cantidad_provincias.short_description = 'Provincias'

    def cantidad_comunas(self, obj):
        return sum(p.comunas.count() for p in obj.provincias.all())
    cantidad_comunas.short_description = 'Comunas'


@admin.register(Provincia)
class ProvinciaAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'region',
        'orden',
        'cantidad_comunas',
    ]
    list_filter = [
        ('region', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['nombre', 'region__nombre', 'region__codigo_romano']
    list_editable = ['orden']
    ordering = ['region__orden', 'orden', 'nombre']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['region']
    inlines = [ComunaInline]

    def cantidad_comunas(self, obj):
        return obj.comunas.count()
    cantidad_comunas.short_description = 'Comunas'


@admin.register(Comuna)
class ComunaAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'provincia',
        'region_display',
        'orden',
    ]
    list_filter = [
        ('provincia__region', admin.RelatedOnlyFieldListFilter),
        ('provincia', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'nombre',
        'provincia__nombre',
        'provincia__region__nombre',
        'provincia__region__codigo_romano',
    ]
    list_editable = ['orden']
    ordering = ['provincia__region__orden', 'provincia__orden', 'orden', 'nombre']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['provincia']

    def region_display(self, obj):
        return obj.provincia.region.codigo_romano
    region_display.short_description = 'Región'
    region_display.admin_order_field = 'provincia__region__orden'


@admin.register(Rubro)
class RubroAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'tipo',
        'icono',
        'activo',
        'es_otro',
        'orden',
    ]
    list_filter = ['tipo', 'activo', 'es_otro']
    search_fields = ['nombre', 'slug', 'descripcion']
    list_editable = ['orden', 'activo', 'icono']
    readonly_fields = ['id', 'slug', 'fecha_creacion', 'fecha_actualizacion']
    ordering = ['orden', 'nombre']
    prepopulated_fields = {}
