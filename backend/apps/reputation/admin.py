from django.contrib import admin
from .models import ResenaGoogle, Benchmark


@admin.register(ResenaGoogle)
class ResenaGoogleAdmin(admin.ModelAdmin):
    list_display = ['id', 'local', 'autor_nombre', 'calificacion', 'sentimiento', 'fecha_google', 'fecha_captura', 'corregido_por_usuario']
    list_filter = ['calificacion', 'sentimiento', 'sentimiento_corregido', 'corregido_por_usuario', 'fecha_captura']
    search_fields = ['autor_nombre', 'comentario', 'google_review_id']
    readonly_fields = ['id', 'fecha_captura']
    raw_id_fields = ['local']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Benchmark)
class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ['id', 'local', 'fecha_generacion', 'posicion_local', 'total_evaluados', 'puntuacion_local', 'puntuacion_promedio_rubro', 'top25_promedio', 'bottom25_promedio']
    list_filter = ['fecha_generacion']
    search_fields = ['local__nombre']
    readonly_fields = ['id', 'fecha_generacion']
    raw_id_fields = ['local']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False
