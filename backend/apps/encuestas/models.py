import uuid
from django.db import models
from django.db.models import TextChoices


class EmocionCSATChoices(TextChoices):
    MUY_FELIZ = 'MUY_FELIZ', 'Muy Feliz (5/5)'
    FELIZ = 'FELIZ', 'Feliz (4/5)'
    NEUTRAL = 'NEUTRAL', 'Neutral (3/5)'
    INSATISFECHO = 'INSATISFECHO', 'Insatisfecho (2/5)'
    MUY_INSATISFECHO = 'MUY_INSATISFECHO', 'Muy Insatisfecho (1/5)'


class OrigenRespuestaChoices(TextChoices):
    QR_IMPRESO = 'QR_IMPRESO', 'QR impreso en local'
    QR_WEB = 'QR_WEB', 'Código QR web / link directo'
    MANUAL = 'MANUAL', 'Registro manual de cliente'
    EMAIL = 'EMAIL', 'Invitación por email'


class PlantillaEncuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150, verbose_name='Nombre interno plantilla')
    nombre_mostrar = models.CharField(max_length=200, blank=True, null=True, verbose_name='Título público')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción para el cliente')
    orden = models.IntegerField(default=10, verbose_name='Orden visual')

    # Preguntas y flags
    activar_nps = models.BooleanField(default=True, verbose_name='Pregunta NPS (0-10)')
    titulo_nps = models.CharField(max_length=200, default='¿Qué tan probable es que nos recomiendes a un familiar o amigo?', verbose_name='Título pregunta NPS')
    activar_csat = models.BooleanField(default=True, verbose_name='Pregunta CSAT (Carita de satisfacción')
    titulo_csat = models.CharField(max_length=200, default='¿Qué tan satisfecho estás con la atención recibida hoy?', verbose_name='Título pregunta CSAT')
    activar_comentario = models.BooleanField(default=True, verbose_name='Comentario libre')
    titulo_comentario = models.CharField(max_length=200, default='¿Quieres agregar un comentario sobre tu experiencia? (opcional)', verbose_name='Título campo comentario')
    comentario_requerido = models.BooleanField(default=False, verbose_name='Comentario obligatorio')
    preguntas_extra = models.JSONField(default=list, blank=True, verbose_name='Preguntas extra custom JSON (futuro')

    # Visibilidad y rubros
    rubros = models.ManyToManyField('geo.Rubro', blank=True, related_name='plantillas_encuesta', verbose_name='Rubros donde se aplica (vacío = todos')
    activa = models.BooleanField(default=True, verbose_name='Plantilla activa')
    es_default = models.BooleanField(default=False, verbose_name='Plantilla default para nuevos locales')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Fecha actualización')

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Plantilla de encuesta'
        verbose_name_plural = 'Plantillas de encuestas'

    def __str__(self):
        return f'{self.nombre} (Default: {"SI" if self.es_default else "NO"} · {"Activa" if self.activa else "Inactiva"})'



class RespuestaEncuesta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local = models.ForeignKey(
        'businesses.Local',
        on_delete=models.CASCADE,
        related_name='respuestas_encuesta',
        verbose_name='Local QR'
    )
    plantilla = models.ForeignKey(
        PlantillaEncuesta,
        on_delete=models.SET_NULL,
        related_name='respuestas',
        blank=True,
        null=True,
        verbose_name='Plantilla usada'
    )
    nps_puntaje = models.IntegerField(
        verbose_name='NPS (0-10)')
    csat_emocion = models.CharField(
        max_length=30,
        choices=EmocionCSATChoices.choices,
        blank=True,
        null=True,
        verbose_name='CSAT emoción')
    comentario = models.TextField(blank=True, null=True, verbose_name='Comentario cliente')
    email_opcional = models.EmailField(blank=True, null=True, verbose_name='Email cliente (opcional, para contacto)')
    origen = models.CharField(
        max_length=30,
        choices=OrigenRespuestaChoices.choices,
        default=OrigenRespuestaChoices.QR_IMPRESO,
        verbose_name='Origen respuesta'
    )
    es_anonima = models.BooleanField(default=False, verbose_name='Cliente autoriza ser contactado')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata navegador/dispositivo')
    fecha_respuesta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora de respuesta')

    def nps_categoria(self):
        if self.nps_puntaje is None:
            return 'Sin dato'
        n = self.nps_puntaje
        if n >= 9:
            return 'Promotor'
        elif n >= 7:
            return 'Pasivo'
        else:
            return 'Detractor'

    class Meta:
        ordering = ['-fecha_respuesta']
        verbose_name = 'Respuesta de encuesta'
        verbose_name_plural = 'Respuestas de encuestas'
        indexes = [
            models.Index(fields=['local', '-fecha_respuesta']),
            models.Index(fields=['local_id']),
        ]

    def __str__(self):
        nps_txt = f'NPS {self.nps_puntaje}' if self.nps_puntaje is not None else 'sin NPS'
        local_nombre = self.local.nombre[:20] if self.local else 'sin local'
        return f'Respuesta {str(self.id)[:8]}... {nps_txt} | local={local_nombre}'
