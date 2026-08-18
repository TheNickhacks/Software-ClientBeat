import uuid
from django.db import models
from django.db.models import TextChoices
from django.core.validators import MaxValueValidator, MinValueValidator


class TipoEncuestaChoices(TextChoices):
    NPS = 'NPS', 'NPS'
    CSAT = 'CSAT', 'CSAT'
    MIXTO = 'MIXTO', 'Mixto'


class SentimientoChoices(TextChoices):
    POSITIVO = 'POSITIVO', 'Positivo'
    NEUTRO = 'NEUTRO', 'Neutro'
    NEGATIVO = 'NEGATIVO', 'Negativo'


class PlantillaEncuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=10, choices=TipoEncuestaChoices.choices)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    preguntas = models.JSONField(default=dict)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plantilla de encuesta'
        verbose_name_plural = 'Plantillas de encuesta'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'


class Encuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local = models.ForeignKey(
        'businesses.Local',
        related_name='encuestas',
        on_delete=models.CASCADE
    )
    plantilla = models.ForeignKey(
        PlantillaEncuesta,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    token = models.CharField(max_length=100, unique=True)
    url_qr = models.CharField(max_length=500, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Encuesta'
        verbose_name_plural = 'Encuestas'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Encuesta {self.id} - Local {self.local_id}'


class RespuestaEncuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    encuesta = models.ForeignKey(
        Encuesta,
        related_name='respuestas',
        on_delete=models.CASCADE
    )
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    csat_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nps_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    comentario = models.TextField(null=True, blank=True)
    enviado_google = models.BooleanField(default=False)
    datos = models.JSONField(null=True, blank=True)
    sentimiento = models.CharField(
        max_length=10,
        choices=SentimientoChoices.choices,
        null=True,
        blank=True
    )
    score_sentimiento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    dispositivo = models.CharField(max_length=100, null=True, blank=True)
    navegador = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'Respuesta de encuesta'
        verbose_name_plural = 'Respuestas de encuesta'
        ordering = ['-fecha_respuesta']

    def __str__(self):
        return f'Respuesta {self.id} - Encuesta {self.encuesta_id}'


class PreguntaRespuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    respuesta = models.ForeignKey(
        RespuestaEncuesta,
        related_name='preguntas_respuestas',
        on_delete=models.CASCADE
    )
    pregunta_texto = models.CharField(max_length=500)
    respuesta_texto = models.TextField(null=True, blank=True)
    respuesta_valor = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Pregunta y respuesta'
        verbose_name_plural = 'Preguntas y respuestas'

    def __str__(self):
        return f'{self.pregunta_texto[:50]}...'
