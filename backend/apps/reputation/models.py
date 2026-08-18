import uuid
from django.db import models
from django.db.models import TextChoices


class SentimientoChoices(TextChoices):
    POSITIVO = 'POSITIVO', 'Positivo'
    NEUTRO = 'NEUTRO', 'Neutro'
    NEGATIVO = 'NEGATIVO', 'Negativo'


class ResenaGoogle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local = models.ForeignKey('businesses.Local', on_delete=models.CASCADE, related_name='resenas')
    google_review_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    autor_nombre = models.CharField(max_length=255)
    autor_foto_url = models.CharField(max_length=500, null=True, blank=True)
    calificacion = models.IntegerField()
    comentario = models.TextField(null=True, blank=True)
    fecha_google = models.DateTimeField()
    fecha_captura = models.DateTimeField(auto_now_add=True)
    sentimiento = models.CharField(max_length=10, choices=SentimientoChoices.choices, null=True, blank=True)
    score_sentimiento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    corregido_por_usuario = models.BooleanField(default=False)
    sentimiento_corregido = models.CharField(max_length=10, choices=SentimientoChoices.choices, null=True, blank=True)

    class Meta:
        verbose_name = 'Reseña Google'
        verbose_name_plural = 'Reseñas Google'
        ordering = ['-fecha_google']

    def __str__(self):
        return f'{self.autor_nombre} - {self.calificacion}★'


class Benchmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local = models.ForeignKey('businesses.Local', on_delete=models.CASCADE, related_name='benchmarks')
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    posicion_local = models.IntegerField()
    total_evaluados = models.IntegerField()
    puntuacion_local = models.DecimalField(max_digits=5, decimal_places=2)
    puntuacion_promedio_rubro = models.DecimalField(max_digits=5, decimal_places=2)
    top25_promedio = models.DecimalField(max_digits=5, decimal_places=2)
    bottom25_promedio = models.DecimalField(max_digits=5, decimal_places=2)
    datos = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Benchmark'
        verbose_name_plural = 'Benchmarks'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f'Benchmark {self.local} - {self.fecha_generacion.strftime("%d/%m/%Y")}'
