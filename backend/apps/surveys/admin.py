from django.contrib import admin

from .models import (
    PlantillaEncuesta,
    Encuesta,
    RespuestaEncuesta,
    PreguntaRespuesta,
)


@admin.register(PlantillaEncuesta)
class PlantillaEncuestaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'activa', 'fecha_creacion')
    list_filter = ('tipo', 'activa', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')


@admin.register(Encuesta)
class EncuestaAdmin(admin.ModelAdmin):
    list_display = ('id', 'local', 'plantilla', 'token', 'fecha_creacion', 'fecha_ultima_respuesta')
    list_filter = ('fecha_creacion', 'fecha_ultima_respuesta')
    search_fields = ('token', 'local__id', 'url_qr')
    readonly_fields = ('id', 'fecha_creacion')


@admin.register(RespuestaEncuesta)
class RespuestaEncuestaAdmin(admin.ModelAdmin):
    list_display = ('id', 'encuesta', 'fecha_respuesta', 'csat_score', 'nps_score', 'sentimiento', 'score_sentimiento', 'enviado_google')
    list_filter = ('fecha_respuesta', 'sentimiento', 'enviado_google')
    search_fields = ('comentario', 'dispositivo', 'navegador')
    readonly_fields = ('id', 'fecha_respuesta')


@admin.register(PreguntaRespuesta)
class PreguntaRespuestaAdmin(admin.ModelAdmin):
    list_display = ('id', 'respuesta', 'pregunta_texto', 'respuesta_valor')
    search_fields = ('pregunta_texto', 'respuesta_texto')
    readonly_fields = ('id',)
