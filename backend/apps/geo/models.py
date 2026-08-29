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


class GoogleCategory(models.Model):
    """Catálogo oficial Google Places API: ~96 categories (33 principales con subratings visibles).
    Fuente: Metodología.xlsx hoja "Listado rubros" + google_review_fields_by_category.csv.
    """
    google_en = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Google category (EN)',
        help_text='Identificador Google Places API: bakery, restaurant, hair_care, etc.'
    )
    google_es = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre amigable (ES)'
    )
    has_visible_subratings = models.BooleanField(
        default=False,
        verbose_name='Tiene subratings visibles en Google (Food/Service/Atmosphere/...)',
        help_text='bakery/bar/cafe/restaurant/hair_care/beauty_salon = True (33 principales lo tienen).'
    )
    subratings_examples = models.JSONField(
        default=list,
        blank=True,
        help_text='Ej: ["Food & Drink quality", "Service", "Atmosphere & Ambience"]'
    )
    additional_fields = models.JSONField(
        default=list,
        blank=True,
        help_text='Otros campos Google medibles: ["spend_per_person", "popular_times", ...]'
    )
    documentation_note = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0, db_index=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Google Category'
        verbose_name_plural = 'Google Categories'
        ordering = ['orden', 'google_es', 'google_en']

    def __str__(self):
        return self.google_es or self.google_en


class RubroDimension(models.Model):
    """4 Dimensiones por Rubro definidas en Metodología.xlsx hoja "Análisis Reseñas":
    Atención al Cliente / Producto / Espacio / Limpieza e Higiene (y 5ta específica por rubro).
    """
    class TipoDimension(models.TextChoices):
        ATENCION = 'ATENCION', 'Atención al Cliente'
        PRODUCTO = 'PRODUCTO', 'Producto / Servicio'
        ESPACIO = 'ESPACIO', 'Espacio / Ambiente'
        LIMPIEZA = 'LIMPIEZA', 'Limpieza e Higiene'
        ESPECIFICA_RUBRO = 'ESPECIFICA_RUBRO', 'Específica del Rubro'

    rubro = models.ForeignKey(
        'Rubro',
        on_delete=models.CASCADE,
        related_name='dimensiones',
        verbose_name='Rubro'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TipoDimension.choices,
        default=TipoDimension.ATENCION,
        verbose_name='Tipo de Dimensión'
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre dimensión (mostrar en UI)'
    )
    descripcion = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dimensión Rubro'
        verbose_name_plural = 'Dimensiones Rubros'
        ordering = ['rubro__orden', 'orden', 'tipo']
        unique_together = [['rubro', 'nombre']]

    def __str__(self):
        return f'{self.rubro.nombre} · {self.nombre}'


class RubroDimensionAtributo(models.Model):
    """Atributo concreto dentro de una Dimensión (ej: Dimensión Atención → Atributo "Velocidad atención", "Amabilidad empleados").
    28 rubros × 4 dimensiones × ~8 atributos = ~900 atributos.
    """
    dimension = models.ForeignKey(
        RubroDimension,
        on_delete=models.CASCADE,
        related_name='atributos',
        verbose_name='Dimensión'
    )
    nombre = models.CharField(
        max_length=255,
        verbose_name='Nombre atributo (keyword detectar en reseña)'
    )
    sinonimos = models.JSONField(
        default=list,
        blank=True,
        help_text='Keywords adicionales para match en reseñas (sinónimos, variantes).'
    )
    ponderacion = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Ponderación para cálculo score dimensión'
    )
    orden = models.PositiveSmallIntegerField(default=0, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Atributo Dimensión'
        verbose_name_plural = 'Atributos Dimensiones'
        ordering = ['dimension__rubro__orden', 'dimension__orden', 'orden', 'nombre']
        unique_together = [['dimension', 'nombre']]

    def __str__(self):
        return f'{self.dimension.rubro.nombre} · {self.dimension.nombre} · {self.nombre}'


class Rubro(models.Model):
    class TipoClasificacion(models.TextChoices):
        PRODUCTO = 'PRODUCTO', 'Producto'
        SERVICIO = 'SERVICIO', 'Servicio'
        MIXTO = 'MIXTO', 'Producto y Servicio'

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
    rubro_principal_1 = models.CharField(
        max_length=20,
        choices=TipoClasificacion.choices,
        default=TipoClasificacion.MIXTO,
        verbose_name='Rubro Principal 1 (Producto/Servicio/Mixto)'
    )
    rubro_principal_2 = models.CharField(
        max_length=20,
        choices=TipoClasificacion.choices,
        blank=True,
        null=True,
        verbose_name='Rubro Principal 2 (opcional, sub-rubro mixto)'
    )
    google_category = models.ForeignKey(
        GoogleCategory,
        on_delete=models.SET_NULL,
        related_name='rubros_primary',
        blank=True,
        null=True,
        verbose_name='Google Category principal (FK)'
    )
    google_categories = models.ManyToManyField(
        GoogleCategory,
        blank=True,
        related_name='rubros',
        verbose_name='Google Categories asociadas (M2M)'
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
