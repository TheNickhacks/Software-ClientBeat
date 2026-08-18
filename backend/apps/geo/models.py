from django.db import models
from django.utils.text import slugify


class Region(models.Model):
    nombre = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Nombre de Región',
        help_text='Ejemplo: Metropolitana de Santiago, Valparaíso, Biobío, etc.'
    )
    codigo_romano = models.CharField(
        max_length=8,
        unique=True,
        verbose_name='Código Romano / Oficial',
        help_text='Ej: RM, I, II, XV, etc.'
    )
    orden = models.PositiveSmallIntegerField(
        default=0,
        db_index=True,
        verbose_name='Orden de despliegue (1..16)'
    )
    activo = models.BooleanField(default=True, verbose_name='Activa en Onboarding')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return f'{self.codigo_romano} - {self.nombre}'


class Provincia(models.Model):
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='provincias',
        verbose_name='Región'
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre de Provincia'
    )
    orden = models.PositiveSmallIntegerField(default=0, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'
        ordering = ['region__orden', 'orden', 'nombre']
        unique_together = [['region', 'nombre']]

    def __str__(self):
        return f'{self.nombre} ({self.region.codigo_romano})'


class Comuna(models.Model):
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='comunas',
        verbose_name='Provincia'
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre de Comuna'
    )
    orden = models.PositiveSmallIntegerField(default=0, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'
        ordering = ['provincia__region__orden', 'provincia__orden', 'orden', 'nombre']
        unique_together = [['provincia', 'nombre']]

    def __str__(self):
        return f'{self.nombre} - {self.provincia.nombre} - {self.provincia.region.codigo_romano}'

    @property
    def region(self):
        return self.provincia.region


class Rubro(models.Model):
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Nombre del Rubro'
    )
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    descripcion = models.TextField(
        blank=True,
        help_text='Descripción breve (aparece en onboarding como ayuda al dueño).'
    )
    icono = models.CharField(
        max_length=60,
        blank=True,
        help_text='Clase FontAwesome o emoji para mostrar en UI (ej: fa-mug-hot, 🍕).'
    )
    tipo = models.CharField(
        max_length=30,
        default='LOCAL_FISICO',
        choices=[
            ('LOCAL_FISICO', 'Local físico (restaurante, local, comercio)'),
            ('RUBRO_ONLINE', 'Rubro online / e-commerce / digital'),
            ('AMBOS', 'Mixto (físico + online)'),
        ],
        db_index=True,
        verbose_name='Tipo de Rubro'
    )
    activo = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Activo en onboarding (lista desplegable)'
    )
    es_otro = models.BooleanField(
        default=False,
        verbose_name='Opción "Otro / No está en la lista"'
    )
    orden = models.PositiveSmallIntegerField(default=0, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rubro'
        verbose_name_plural = 'Rubros'
        ordering = ['orden', 'nombre']

    def __str__(self):
        base = self.nombre
        if self.es_otro:
            base += ' (Otro)'
        if self.tipo != 'LOCAL_FISICO':
            base += f' [{self.get_tipo_display()}]'
        return base

    def save(self, *args, **kwargs):
        if not self.slug and self.nombre:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
