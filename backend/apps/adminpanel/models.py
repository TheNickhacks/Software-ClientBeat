import uuid
from django.conf import settings
from django.db import models
from django.db.models import TextChoices


class AccionAuditoriaChoices(TextChoices):
    CREAR = 'CREAR', 'Crear'
    EDITAR = 'EDITAR', 'Editar'
    ELIMINAR = 'ELIMINAR', 'Eliminar'
    ACTIVAR = 'ACTIVAR', 'Activar'
    DESACTIVAR = 'DESACTIVAR', 'Desactivar'
    SUSPENDER = 'SUSPENDER', 'Suspender'
    CONFIRMAR = 'CONFIRMAR', 'Confirmar'
    CANCELAR = 'CANCELAR', 'Cancelar'
    CAMBIAR_PLAN = 'CAMBIAR_PLAN', 'Cambiar Plan'
    EXTENDER_DIAS = 'EXTENDER_DIAS', 'Extender Días'
    REINICIAR_ONBOARDING = 'REINICIAR_ONBOARDING', 'Reiniciar Onboarding'
    RESETEAR_CLAVE = 'RESETEAR_CLAVE', 'Resetear Clave'
    CAMBIAR_ROL = 'CAMBIAR_ROL', 'Cambiar Rol'
    REASIGNAR_DUENO = 'REASIGNAR_DUENO', 'Reasignar Dueño'
    MARCAR_DEFAULT = 'MARCAR_DEFAULT', 'Marcar Default'
    CORREGIR_SENTIMIENTO = 'CORREGIR_SENTIMIENTO', 'Corregir Sentimiento'
    SEED_DATOS = 'SEED_DATOS', 'Seed / Cargar Datos'
    OTRO = 'OTRO', 'Otro'


class ModuloAuditoriaChoices(TextChoices):
    SUSCRIPCIONES = 'SUSCRIPCIONES', 'Suscripciones'
    NEGOCIOS = 'NEGOCIOS', 'Negocios'
    USUARIOS = 'USUARIOS', 'Usuarios'
    PLANES = 'PLANES', 'Planes'
    PLANTILLAS_ENCUESTAS = 'PLANTILLAS_ENCUESTAS', 'Plantillas Encuestas'
    PLANTILLAS_NOTIFICACIONES = 'PLANTILLAS_NOTIFICACIONES', 'Plantillas Notificaciones'
    RUBROS = 'RUBROS', 'Rubros'
    LOCALES = 'LOCALES', 'Locales'
    PAGOS = 'PAGOS', 'Pagos'
    COBROS = 'COBROS', 'Cobros'
    RESEÑAS_GOOGLE = 'RESEÑAS_GOOGLE', 'Reseñas Google'
    RESPUESTAS_ENCUESTA = 'RESPUESTAS_ENCUESTA', 'Respuestas Encuesta'
    BENCHMARK = 'BENCHMARK', 'Benchmark'
    OTRO = 'OTRO', 'Otro'


class AuditoriaAdmin(models.Model):
    """Registro completo de auditoría de cada acción realizada en el Panel Admin Soporte (NO-técnico).
    Objetivo: trazabilidad total sin necesidad de entrar a /admin/ Django."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias_admin',
        verbose_name='Administrador que realizó la acción',
    )
    usuario_email = models.EmailField(
        blank=True,
        null=True,
        help_text='Cache del email por si el usuario se elimina posteriormente.',
    )
    accion = models.CharField(max_length=30, choices=AccionAuditoriaChoices.choices, db_index=True)
    modulo = models.CharField(max_length=30, choices=ModuloAuditoriaChoices.choices, db_index=True)
    entidad_tipo = models.CharField(
        max_length=100,
        help_text='Nombre del modelo: ej. Suscripcion, Negocio, Plan, User',
    )
    entidad_id = models.CharField(max_length=255, help_text='UUID o ID de la entidad afectada.')
    entidad_descripcion = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Descripción amigable: ej. "Café del Centro Demo - Plan MVP_Básico".',
    )

    datos_antes = models.JSONField(
        default=dict,
        blank=True,
        help_text='Estado anterior de la entidad (dict).',
    )
    datos_despues = models.JSONField(
        default=dict,
        blank=True,
        help_text='Estado posterior de la entidad (dict).',
    )
    notas_internas = models.TextField(
        blank=True,
        null=True,
        help_text='Notas que escribe el Admin Soporte al ejecutar la acción.',
    )
    ip_origen = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Auditoría Admin Soporte'
        verbose_name_plural = 'Auditorías Admin Soporte'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['modulo', 'accion', '-fecha_hora']),
            models.Index(fields=['entidad_tipo', 'entidad_id']),
            models.Index(fields=['usuario', '-fecha_hora']),
        ]

    def __str__(self):
        return f'[{self.fecha_hora:%d/%m/%Y %H:%M}] {self.get_accion_display()} · {self.get_modulo_display()} · {self.usuario_email or "Sistema"}'

    @classmethod
    def registrar(cls, request, accion, modulo, entidad, *, descripcion=None, datos_antes=None, datos_despues=None, notas=None):
        """Helper para registrar una auditoría desde una vista Django (tiene request)."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if isinstance(entidad, models.Model):
            entidad_tipo = entidad.__class__.__name__
            entidad_id = str(entidad.pk)
        else:
            entidad_tipo = str(entidad.__class__.__name__) if hasattr(entidad, '__class__') else 'Unknown'
            entidad_id = str(entidad) if entidad else ''
        return cls.objects.create(
            usuario=request.user if request and hasattr(request, 'user') and isinstance(request.user, User) else None,
            usuario_email=getattr(request.user, 'email', None) if request and hasattr(request, 'user') else None,
            accion=accion,
            modulo=modulo,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            entidad_descripcion=descripcion or (str(entidad) if entidad and hasattr(entidad, '__str__') else None),
            datos_antes=datos_antes or {},
            datos_despues=datos_despues or {},
            notas_internas=notas,
            ip_origen=cls._get_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request and hasattr(request, 'META') else None,
        )

    @staticmethod
    def _get_ip(request):
        if not request or not hasattr(request, 'META'):
            return None
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
