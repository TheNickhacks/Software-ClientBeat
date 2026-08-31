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


class ConfiguracionMetricas(models.Model):
    """Configuración global de criterios metodológicos para Benchmark, CSAT/NPS y Reseñas Google."""
    
    TEMPORAL_CHOICES = [
        ('SEMANAL', 'Semanal'),
        ('MENSUAL', 'Mensual'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
    ]

    GEOGRAFICO_CHOICES = [
        ('5KM', 'Hasta 5 km'),
        ('COMUNAL', 'Comunal'),
        ('REGIONAL', 'Regional'),
        ('NACIONAL', 'Nacional'),
    ]

    DESEMPATE_CHOICES = [
        ('DECIMAS', 'Décimas de valoración'),
        ('POSITIVAS_PERIODO', 'Valoraciones positivas del último mes/semestre'),
    ]

    # 3.1 Benchmark (Google & ClientBeat)
    bm_min_empresas = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas en el benchmark'
    )
    bm_min_valoraciones = models.PositiveIntegerField(
        default=10,
        verbose_name='Cantidad mínima de valoraciones requeridas'
    )
    bm_dias_sin_valoraciones_excluir = models.PositiveIntegerField(
        default=90,
        verbose_name='Días sin valoraciones para excluir del benchmark'
    )
    bm_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal predeterminado'
    )
    bm_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico predeterminado'
    )
    bm_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate'
    )
    bm_nota_explicativa_usuario = models.TextField(
        default='Los criterios de benchmark determinan la muestra mínima de empresas y opiniones requeridas para comparar el rendimiento de tu negocio en tu rubro y zona geográfica.',
        verbose_name='Explicación de criterios visible en Dashboard de Usuario'
    )

    # 3.2 CSAT y NPS
    csat_nps_criterio_metodologico = models.TextField(
        default='CSAT (% respuestas de 4 y 5 estrellas / caritas felices) y NPS (% Promotores [9-10] menos % Detractores [0-6]).',
        verbose_name='Criterio metodológico de cálculo'
    )
    csat_nps_min_empresas_benchmark = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas para benchmark por rubro'
    )
    csat_nps_min_valoraciones = models.PositiveIntegerField(
        default=5,
        verbose_name='Cantidad mínima de valoraciones para aparecer en benchmark'
    )
    csat_nps_dias_sin_valoraciones_excluir = models.PositiveIntegerField(
        default=60,
        verbose_name='Días sin valoraciones para excluir del benchmark'
    )
    csat_nps_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal default CSAT/NPS'
    )
    csat_nps_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico default CSAT/NPS'
    )
    csat_nps_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate CSAT/NPS'
    )

    # 3.3 Reseñas Google
    resenas_minimo_para_analisis = models.PositiveIntegerField(
        default=5,
        verbose_name='Mínimo de reseñas para realizar análisis'
    )
    resenas_categorias_agrupacion = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Categorías de agrupación de reseñas'
    )
    resenas_dias_sin_valoraciones_no_mostrar = models.PositiveIntegerField(
        default=120,
        verbose_name='Rango de tiempo sin valoraciones para ocultar análisis en la app'
    )

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Métricas'
        verbose_name_plural = 'Configuración de Métricas'

    def __str__(self):
        return f'Configuración de Métricas (Actualizada {self.fecha_actualizacion:%d/%m/%Y %H:%M})'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        if not obj.resenas_categorias_agrupacion:
            obj.resenas_categorias_agrupacion = [
                'Atención al Cliente',
                'Calidad de Producto / Servicio',
                'Ambiente y Limpieza',
                'Tiempos de Espera',
                'Relación Precio / Calidad'
            ]
            obj.save(update_fields=['resenas_categorias_agrupacion'])
        return obj

