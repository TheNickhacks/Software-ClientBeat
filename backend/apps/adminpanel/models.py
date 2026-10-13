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

    # ----------------------------------------------------
    # CAMPOS LEGACY (compatibilidad retroactiva)
    # ----------------------------------------------------
    bm_min_empresas = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas en el benchmark (Legacy)'
    )
    bm_min_valoraciones = models.PositiveIntegerField(
        default=10,
        verbose_name='Cantidad mínima de valoraciones requeridas (Legacy)'
    )
    bm_dias_sin_valoraciones_excluir = models.PositiveIntegerField(
        default=90,
        verbose_name='Días sin valoraciones para excluir del benchmark (Legacy)'
    )
    bm_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal predeterminado (Legacy)'
    )
    bm_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico predeterminado (Legacy)'
    )
    bm_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate (Legacy)'
    )
    bm_nota_explicativa_usuario = models.TextField(
        default='Los criterios de benchmark determinan la muestra mínima de empresas y opiniones requeridas para comparar el rendimiento de tu negocio en tu rubro y zona geográfica.',
        verbose_name='Explicación de criterios visible en Dashboard de Usuario (Legacy)'
    )
    csat_nps_criterio_metodologico = models.TextField(
        default='CSAT (% respuestas de 4 y 5 estrellas / caritas felices) y NPS (% Promotores [9-10] menos % Detractores [0-6]).',
        verbose_name='Criterio metodológico de cálculo (Legacy)'
    )
    csat_nps_min_empresas_benchmark = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas para benchmark por rubro (Legacy)'
    )
    csat_nps_min_valoraciones = models.PositiveIntegerField(
        default=5,
        verbose_name='Cantidad mínima de valoraciones para aparecer en benchmark (Legacy)'
    )
    csat_nps_dias_sin_valoraciones_excluir = models.PositiveIntegerField(
        default=60,
        verbose_name='Días sin valoraciones para excluir del benchmark (Legacy)'
    )
    csat_nps_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal default CSAT/NPS (Legacy)'
    )
    csat_nps_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico default CSAT/NPS (Legacy)'
    )
    csat_nps_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate CSAT/NPS (Legacy)'
    )

    # ====================================================
    # 1. CRITERIOS BENCHMARK GOOGLE (Independiente)
    # ====================================================
    bm_google_min_empresas = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas en Benchmark Google'
    )
    bm_google_min_valoraciones = models.PositiveIntegerField(
        default=10,
        verbose_name='Cantidad mínima de opiniones Google requeridas'
    )
    bm_google_dias_sin_valoraciones_excluir = models.PositiveIntegerField(
        default=90,
        verbose_name='Días sin opiniones para excluir en Benchmark Google'
    )
    bm_google_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal predeterminado Benchmark Google'
    )
    bm_google_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico predeterminado Benchmark Google'
    )
    bm_google_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate Benchmark Google'
    )
    bm_google_nota_explicativa_usuario = models.TextField(
        default='Los criterios de Benchmark Google determinan la muestra mínima de competidores y opiniones públicas en Google Maps para calcular los promedios de tu rubro y zona geográfica.',
        verbose_name='Nota explicativa Benchmark Google en Dashboard'
    )

    # ====================================================
    # 2. CRITERIOS BENCHMARK CLIENTBEAT (Independiente)
    # ====================================================
    bm_clientbeat_min_empresas = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas en Benchmark ClientBeat'
    )
    bm_clientbeat_min_respuestas = models.PositiveIntegerField(
        default=15,
        verbose_name='Cantidad mínima de respuestas de encuesta ClientBeat requeridas'
    )
    bm_clientbeat_dias_sin_respuestas_excluir = models.PositiveIntegerField(
        default=60,
        verbose_name='Días sin respuestas para excluir en Benchmark ClientBeat'
    )
    bm_clientbeat_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal predeterminado Benchmark ClientBeat'
    )
    bm_clientbeat_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico predeterminado Benchmark ClientBeat'
    )
    bm_clientbeat_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate Benchmark ClientBeat'
    )
    bm_clientbeat_nota_explicativa_usuario = models.TextField(
        default='Los criterios de Benchmark ClientBeat se basan exclusivamente en evaluaciones directas de clientes obtenidas mediante encuestas QR en establecimientos registrados en la plataforma.',
        verbose_name='Nota explicativa Benchmark ClientBeat en Dashboard'
    )

    # ====================================================
    # 3. CRITERIOS INDICADOR CSAT (Independiente)
    # ====================================================
    csat_criterio_metodologico = models.TextField(
        default='CSAT (Customer Satisfaction Score): Porcentaje de evaluaciones con valoración positiva (4 y 5 estrellas o Muy Satisfecho / Feliz) sobre el total de respuestas recibidas en el período.',
        verbose_name='Criterio metodológico de cálculo CSAT'
    )
    csat_min_empresas_benchmark = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas para benchmark CSAT'
    )
    csat_min_respuestas = models.PositiveIntegerField(
        default=5,
        verbose_name='Cantidad mínima de respuestas requeridas para calcular CSAT'
    )
    csat_dias_sin_respuestas_excluir = models.PositiveIntegerField(
        default=60,
        verbose_name='Días sin respuestas para excluir del benchmark CSAT'
    )
    csat_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal predeterminado CSAT'
    )
    csat_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico predeterminado CSAT'
    )
    csat_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate CSAT'
    )
    csat_nota_explicativa_usuario = models.TextField(
        default='El índice CSAT mide la satisfacción puntual del cliente con la experiencia recibida en el local o servicio.',
        verbose_name='Nota explicativa CSAT en Dashboard'
    )

    # ====================================================
    # 4. CRITERIOS INDICADOR NPS (Independiente)
    # ====================================================
    nps_criterio_metodologico = models.TextField(
        default='NPS (Net Promoter Score): % Promotores (calificación 9 y 10) menos % Detractores (calificación 0 a 6). Los clientes Pasivos (7 y 8) se consideran en el total pero no en la resta neta.',
        verbose_name='Criterio metodológico de cálculo NPS'
    )
    nps_min_empresas_benchmark = models.PositiveIntegerField(
        default=3,
        verbose_name='Cantidad mínima de empresas para benchmark NPS'
    )
    nps_min_respuestas = models.PositiveIntegerField(
        default=5,
        verbose_name='Cantidad mínima de respuestas requeridas para calcular NPS'
    )
    nps_dias_sin_respuestas_excluir = models.PositiveIntegerField(
        default=60,
        verbose_name='Días sin respuestas para excluir del benchmark NPS'
    )
    nps_filtro_temporal_default = models.CharField(
        max_length=20,
        choices=TEMPORAL_CHOICES,
        default='MENSUAL',
        verbose_name='Filtro temporal predeterminado NPS'
    )
    nps_filtro_geografico_default = models.CharField(
        max_length=20,
        choices=GEOGRAFICO_CHOICES,
        default='COMUNAL',
        verbose_name='Filtro geográfico predeterminado NPS'
    )
    nps_criterio_desempate = models.CharField(
        max_length=30,
        choices=DESEMPATE_CHOICES,
        default='DECIMAS',
        verbose_name='Criterio de desempate NPS'
    )
    nps_nota_explicativa_usuario = models.TextField(
        default='El Net Promoter Score refleja la fidelidad y la probabilidad de que los clientes recomienden tu negocio activamente a amigos o colegas.',
        verbose_name='Nota explicativa NPS en Dashboard'
    )

    # 3.5 Reseñas Google
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

    def save(self, *args, **kwargs):
        # Sincronización automática de campos legacy para retrocompatibilidad
        self.bm_min_empresas = self.bm_google_min_empresas
        self.bm_min_valoraciones = self.bm_google_min_valoraciones
        self.bm_dias_sin_valoraciones_excluir = self.bm_google_dias_sin_valoraciones_excluir
        self.bm_filtro_temporal_default = self.bm_google_filtro_temporal_default
        self.bm_filtro_geografico_default = self.bm_google_filtro_geografico_default
        self.bm_criterio_desempate = self.bm_google_criterio_desempate
        self.bm_nota_explicativa_usuario = self.bm_google_nota_explicativa_usuario

        self.csat_nps_criterio_metodologico = f"{self.csat_criterio_metodologico} | {self.nps_criterio_metodologico}"
        self.csat_nps_min_empresas_benchmark = self.csat_min_empresas_benchmark
        self.csat_nps_min_valoraciones = self.csat_min_respuestas
        self.csat_nps_dias_sin_valoraciones_excluir = self.csat_dias_sin_respuestas_excluir
        self.csat_nps_filtro_temporal_default = self.csat_filtro_temporal_default
        self.csat_nps_filtro_geografico_default = self.csat_filtro_geografico_default
        self.csat_nps_criterio_desempate = self.csat_criterio_desempate
        super().save(*args, **kwargs)

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


class SolicitudARCOPBChoices(TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    EN_PROCESO = 'EN_PROCESO', 'En Proceso'
    RESUELTO = 'RESUELTO', 'Resuelto / Finalizado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'


class SolicitudARCOPB(models.Model):
    """Solicitudes de Derechos ARCOPB (Acceso, Rectificación, Cancelación, Oposición, Portabilidad, Bloqueo - Ley N° 19.628)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_arco'
    )
    nombre_solicitante = models.CharField(max_length=200)
    email_solicitante = models.EmailField()
    rut_solicitante = models.CharField(max_length=20, blank=True, null=True)
    tipo_solicitud = models.CharField(max_length=50, default='ELIMINACION_DATOS')
    detalle = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=SolicitudARCOPBChoices.choices, default=SolicitudARCOPBChoices.PENDIENTE)
    notas_admin = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Solicitud ARCOPB'
        verbose_name_plural = 'Solicitudes ARCOPB'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Solicitud ARCOPB #{str(self.id)[:8]} · {self.email_solicitante} ({self.get_estado_display()})'


