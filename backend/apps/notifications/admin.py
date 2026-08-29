from django.contrib import admin
from .models import PlantillaNotificacion, CategoriaNotificacionChoices


@admin.register(PlantillaNotificacion)
class PlantillaNotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_unico",
        "categoria",
        "nombre",
        "asunto_corto",
        "activo",
        "orden",
        "variables_count",
        "fecha_actualizacion",
    )
    list_filter = (
        "categoria",
        "activo",
        "orden",
        "fecha_creacion",
    )
    search_fields = (
        "codigo_unico",
        "nombre",
        "asunto_email",
        "cuerpo_texto_plano",
        "cuerpo_html",
    )
    readonly_fields = (
        "fecha_creacion",
        "fecha_actualizacion",
    )
    list_editable = ("activo", "orden")
    list_per_page = 30

    fieldsets = (
        (
            "Identificación",
            {
                "fields": (
                    "codigo_unico",
                    "categoria",
                    "nombre",
                    "activo",
                    "orden",
                ),
                "description": "Categorías disponibles: "
                + ", ".join(f"{c[0]} → {c[1]}" for c in CategoriaNotificacionChoices.choices),
            },
        ),
        (
            "Contenido Email",
            {
                "fields": (
                    "asunto_email",
                    "cuerpo_texto_plano",
                    "cuerpo_html",
                ),
            },
        ),
        (
            "Variables y Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    "variables_esperadas",
                    "fecha_creacion",
                    "fecha_actualizacion",
                ),
            },
        ),
    )

    @admin.display(description="Asunto")
    def asunto_corto(self, obj):
        return obj.asunto_email[:60] + ("…" if len(obj.asunto_email) > 60 else "")

    @admin.display(description="# Vars")
    def variables_count(self, obj):
        if isinstance(obj.variables_esperadas, list):
            return len(obj.variables_esperadas)
        return 0
