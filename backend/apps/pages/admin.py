from django.contrib import admin

from .models import PaginaEstatica, PoliticaLegal


@admin.register(PaginaEstatica)
class PaginaEstaticaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'publicado', 'fecha_creacion', 'fecha_actualizacion')
    list_filter = ('publicado', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('titulo', 'slug', 'contenido')
    prepopulated_fields = {'slug': ('titulo',)}
    readonly_fields = ('id', 'fecha_creacion', 'fecha_actualizacion')


@admin.register(PoliticaLegal)
class PoliticaLegalAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'version', 'fecha_vigencia', 'publicado')
    list_filter = ('tipo', 'publicado', 'fecha_vigencia')
    search_fields = ('version', 'contenido')
    readonly_fields = ('id',)
