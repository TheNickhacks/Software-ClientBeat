import uuid
from django.db import models
from django.db.models import TextChoices


class TipoPoliticaChoices(TextChoices):
    TERMINOS_CONDICIONES = 'TERMINOS_CONDICIONES', 'Términos y condiciones'
    POLITICA_PRIVACIDAD = 'POLITICA_PRIVACIDAD', 'Política de privacidad'
    POLITICA_COOKIES = 'POLITICA_COOKIES', 'Política de cookies'


class PaginaEstatica(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.CharField(max_length=200, unique=True)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    publicado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Página estática'
        verbose_name_plural = 'Páginas estáticas'
        ordering = ['titulo']

    def __str__(self):
        return self.titulo


class PoliticaLegal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=30, choices=TipoPoliticaChoices.choices)
    version = models.CharField(max_length=50)
    fecha_vigencia = models.DateField()
    contenido = models.TextField()
    publicado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Política legal'
        verbose_name_plural = 'Políticas legales'
        ordering = ['tipo', '-fecha_vigencia']
        unique_together = ('tipo', 'version')

    def __str__(self):
        return f'{self.get_tipo_display()} - v{self.version}'
