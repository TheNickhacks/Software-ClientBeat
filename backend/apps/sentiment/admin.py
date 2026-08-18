from django.contrib import admin

from .models import DiccionarioSentimiento, HistorialCorreccion


@admin.register(DiccionarioSentimiento)
class DiccionarioSentimientoAdmin(admin.ModelAdmin):
    list_display = ('palabra', 'polaridad', 'peso', 'categoria')
    list_filter = ('polaridad', 'categoria')
    search_fields = ('palabra', 'ejemplo_uso')


@admin.register(HistorialCorreccion)
class HistorialCorreccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'clasificacion_anterior', 'clasificacion_nueva', 'modelo_origen', 'fecha_correccion')
    list_filter = ('clasificacion_anterior', 'clasificacion_nueva', 'fecha_correccion', 'modelo_origen')
    search_fields = ('texto_original',)
    readonly_fields = ('id', 'fecha_correccion')
