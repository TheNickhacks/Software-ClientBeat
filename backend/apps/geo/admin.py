from django.contrib import admin
from apps.accounts.admin_mixins import SuperUserOnlyAdminMixin
from .models import (
    Region, Provincia, Comuna, Rubro,
    GoogleCategory, RubroDimension, RubroDimensionAtributo,
)


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


class RubroDimensionAtributoInline(SuperUserOnlyAdminMixin, admin.TabularInline):
    model = RubroDimensionAtributo
    extra = 0
    fields = ['nombre', 'sinonimos', 'ponderacion', 'orden']
    list_editable = ['orden']


class RubroDimensionInline(SuperUserOnlyAdminMixin, admin.TabularInline):
    model = RubroDimension
    extra = 0
    fields = ['tipo', 'nombre', 'descripcion', 'orden']
    show_change_link = True


@admin.register(Rubro)
class RubroAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre',
        'tipo',
        'rubro_principal_1',
        'rubro_principal_2',
        'google_category',
        'cantidad_dimensiones',
        'icono',
        'activo',
        'es_otro',
        'orden',
    ]
    list_filter = ['tipo', 'activo', 'es_otro', 'rubro_principal_1', 'google_category']
    search_fields = ['nombre', 'slug', 'descripcion']
    list_editable = ['orden', 'activo', 'icono', 'rubro_principal_1']
    readonly_fields = ['id', 'slug', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['google_category']
    filter_horizontal = ['google_categories']
    ordering = ['orden', 'nombre']
    inlines = [RubroDimensionInline]
    prepopulated_fields = {}

    def cantidad_dimensiones(self, obj):
        return obj.dimensiones.count()
    cantidad_dimensiones.short_description = '4D'


@admin.register(GoogleCategory)
class GoogleCategoryAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'google_en',
        'google_es',
        'has_visible_subratings',
        'cantidad_subratings',
        'orden',
        'activo',
    ]
    list_filter = ['has_visible_subratings', 'activo']
    search_fields = ['google_en', 'google_es', 'documentation_note']
    list_editable = ['orden', 'activo', 'google_es', 'has_visible_subratings']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    ordering = ['orden', 'google_en']

    def cantidad_subratings(self, obj):
        return len(obj.subratings_examples or [])
    cantidad_subratings.short_description = 'Subratings'


@admin.register(RubroDimension)
class RubroDimensionAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'rubro',
        'tipo',
        'nombre',
        'cantidad_atributos',
        'orden',
    ]
    list_filter = ['tipo', ('rubro', admin.RelatedOnlyFieldListFilter)]
    search_fields = ['nombre', 'descripcion', 'rubro__nombre']
    list_editable = ['orden', 'nombre']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['rubro']
    ordering = ['rubro__orden', 'orden', 'nombre']
    inlines = [RubroDimensionAtributoInline]

    def cantidad_atributos(self, obj):
        return obj.atributos.count()
    cantidad_atributos.short_description = 'Atributos'


@admin.register(RubroDimensionAtributo)
class RubroDimensionAtributoAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'dimension',
        'nombre',
        'ponderacion',
        'cantidad_sinonimos',
        'orden',
    ]
    list_filter = [
        'ponderacion',
        ('dimension__rubro', admin.RelatedOnlyFieldListFilter),
        ('dimension', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['nombre', 'sinonimos', 'dimension__nombre', 'dimension__rubro__nombre']
    list_editable = ['orden', 'ponderacion']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['dimension']
    ordering = ['dimension__rubro__orden', 'dimension__orden', 'orden', 'nombre']

    def cantidad_sinonimos(self, obj):
        return len(obj.sinonimos or [])
    cantidad_sinonimos.short_description = 'Keywords'
