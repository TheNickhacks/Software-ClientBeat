from django.db import models
from django.utils.text import slugify


class CategoriaNotificacionChoices(models.TextChoices):
    PLANES = "PLANES", "Planes y Suscripciones"
    PAGOS = "PAGOS", "Pagos y Facturación"
    BENCHMARK = "BENCHMARK", "Benchmark y Competencia"
    CSAT_NPS = "CSAT_NPS", "CSAT / NPS y Encuestas"
    RESEÑAS_GOOGLE = "RESEÑAS_GOOGLE", "Reseñas Google"
    ONBOARDING = "ONBOARDING", "Onboarding y Bienvenida"


class PlantillaNotificacion(models.Model):
    codigo_unico = models.SlugField(
        max_length=80,
        unique=True,
        verbose_name="Código Único",
        help_text="Identificador único para uso interno en templates y código.",
    )
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaNotificacionChoices.choices,
        default=CategoriaNotificacionChoices.ONBOARDING,
        verbose_name="Categoría",
        db_index=True,
    )
    nombre = models.CharField(
        max_length=180,
        verbose_name="Nombre Plantilla",
    )
    asunto_email = models.CharField(
        max_length=180,
        verbose_name="Asunto Email",
        help_text="Variable placeholders: {{negocio}}, {{usuario}}, {{local}}, {{kpi}}, etc.",
    )
    cuerpo_texto_plano = models.TextField(
        verbose_name="Cuerpo Texto Plano",
        blank=True,
        default="",
        help_text="Versión texto plano sin HTML para clientes de correo antiguos.",
    )
    cuerpo_html = models.TextField(
        verbose_name="Cuerpo HTML (Django Template)",
        help_text="Puedes usar sintaxis Django Template: {{variable}}, {% for %}, {{nombre|upper}}.",
    )
    variables_esperadas = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Variables Esperadas",
        help_text="Array JSON con nombres de variables a documentar, ej: ['negocio','local','nps_score'].",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activa",
        db_index=True,
    )
    orden = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Orden",
        db_index=True,
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Creación",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización",
    )

    class Meta:
        verbose_name = "Plantilla Notificación"
        verbose_name_plural = "Plantillas Notificaciones"
        ordering = ["categoria", "orden", "nombre"]
        indexes = [
            models.Index(fields=["categoria", "activo"]),
        ]

    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.nombre} ({self.codigo_unico})"

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = slugify(f"{self.categoria}-{self.nombre}")
        super().save(*args, **kwargs)


class Notificacion(models.Model):
    usuario = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    negocio = models.ForeignKey('businesses.Negocio', on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, default='INFO')
    canal = models.CharField(max_length=50, default='IN_APP')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} ({self.usuario or 'Global'})"

