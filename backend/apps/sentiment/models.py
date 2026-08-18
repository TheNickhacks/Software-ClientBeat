import uuid
from django.db import models
from django.db.models import TextChoices


class PolaridadChoices(TextChoices):
    POSITIVO = 'POSITIVO', 'Positivo'
    NEUTRO = 'NEUTRO', 'Neutro'
    NEGATIVO = 'NEGATIVO', 'Negativo'


class CategoriaPalabraChoices(TextChoices):
    MODISMO_CHILENO = 'MODISMO_CHILENO', 'Modismo chileno'
    NEGACION = 'NEGACION', 'Negación'
    INTENSIFICADOR = 'INTENSIFICADOR', 'Intensificador'
    GENERAL = 'GENERAL', 'General'


class DiccionarioSentimiento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    palabra = models.CharField(max_length=100, unique=True)
    polaridad = models.CharField(max_length=10, choices=PolaridadChoices.choices)
    peso = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaPalabraChoices.choices,
        null=True,
        blank=True
    )
    ejemplo_uso = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Diccionario de sentimiento'
        verbose_name_plural = 'Diccionario de sentimientos'
        ordering = ['palabra']

    def __str__(self):
        return f'{self.palabra} ({self.get_polaridad_display()})'


class HistorialCorreccion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    texto_original = models.TextField()
    clasificacion_anterior = models.CharField(max_length=10, choices=PolaridadChoices.choices)
    clasificacion_nueva = models.CharField(max_length=10, choices=PolaridadChoices.choices)
    modelo_origen = models.CharField(max_length=100)
    fecha_correccion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de corrección'
        verbose_name_plural = 'Historiales de corrección'
        ordering = ['-fecha_correccion']

    def __str__(self):
        return f'Corrección {self.id} - {self.fecha_correccion:%d/%m/%Y}'
