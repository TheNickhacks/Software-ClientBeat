import uuid
from django.db import models
from django.db.models import TextChoices


class MonedaChoices(TextChoices):
    CLP = 'CLP', 'Pesos Chilenos'
    UF = 'UF', 'Unidad de Fomento'


class EstadoSuscripcionChoices(TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    ACTIVA = 'ACTIVA', 'Activa'
    VENCIDA = 'VENCIDA', 'Vencida'
    SUSPENDIDA = 'SUSPENDIDA', 'Suspendida'
    CANCELADA = 'CANCELADA', 'Cancelada'


class EstadoPagoChoices(TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    APROBADO = 'APROBADO', 'Aprobado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'
    REEMBOLSADO = 'REEMBOLSADO', 'Reembolsado'


class TipoRegistroCobranzaChoices(TextChoices):
    RECORDATORIO_VENCIMIENTO = 'RECORDATORIO_VENCIMIENTO', 'Recordatorio de Vencimiento'
    SUSPENSION = 'SUSPENSION', 'Suspensión'
    AVISO_VENCIMIENTO = 'AVISO_VENCIMIENTO', 'Aviso de Próximo Vencimiento'
    RECUPERACION = 'RECUPERACION', 'Recuperación de Cobro'
    CONFIRMACION_PAGO = 'CONFIRMACION_PAGO', 'Confirmación de Pago'


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True, default='MVP_BASICO')
    nombre_mostrar = models.CharField(
        max_length=100,
        blank=True,
        help_text='Nombre amigable para mostrar en UI (ej: MVP Básico). Si queda vacío usa "nombre".'
    )
    descripcion = models.TextField(blank=True)
    caracteristicas = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de características del plan en formato JSON: ["📊 Panel de métricas", "📝 Encuestas NPS", ...]'
    )
    precio_uf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_clp = models.IntegerField(null=True, blank=True)
    moneda = models.CharField(max_length=10, choices=MonedaChoices.choices, default=MonedaChoices.CLP)
    locales_permitidos = models.IntegerField(
        default=3,
        help_text='Cantidad TOTAL de locales físicos permitidos (incluye locales gratis antes del cobro extra).'
    )
    usuarios_permitidos = models.IntegerField(default=2)
    # ======= COBRO EXTRA ESCALONADO POR LOCAL (a partir del N° local = locales_gratis_incluidos + 1) =======
    locales_gratis_incluidos = models.IntegerField(
        default=3,
        help_text='Primeros N locales incluidos en el precio base. A partir de N+1 cobra costo_local_adicional_clp por cada uno. Doc: desde 4° local cobra extra (= 3 gratis).'
    )
    costo_local_adicional_clp = models.IntegerField(
        default=0,
        help_text='Costo extra CLP por cada local adicional por sobre locales_gratis_incluidos. (Doc: Basico $30k, Empresarial $25k, Profesional $20k)'
    )
    # ======= RUBROS ONLINE / CROSS-SECTOR =======
    rubros_permitidos = models.IntegerField(
        default=3,
        help_text='Cantidad TOTAL de rubros online permitidos (benchmarking cross-sector / e-commerce).'
    )
    rubros_gratis_incluidos = models.IntegerField(
        default=3,
        help_text='Primeros N rubros online incluidos en el precio base. A partir de N+1 cobra costo_rubro_adicional_clp por cada uno. (Doc: desde 4° rubro online cobra extra)'
    )
    costo_rubro_adicional_clp = models.IntegerField(
        default=0,
        help_text='Costo extra CLP por cada rubro online adicional por sobre rubros_gratis_incluidos. (Doc: Basico $30k, Empresarial $25k, Profesional $20k)'
    )
    rubros = models.ManyToManyField(
        'geo.Rubro',
        blank=True,
        related_name='planes',
        help_text='Rubros online asociados a este plan (para cross-selling / multi-rubro digital).'
    )
    # ======= FEATURE FLAGS PLANES FUNCIONALES (Doc Descripcion App 3 niveles) =======
    tiene_benchmarking_rubro = models.BooleanField(
        default=False,
        help_text='Plan Básico = NO. Empresarial y Profesional = SÍ. Doc: "plan 2 = benchmarking empresas mismo rubro".'
    )
    tiene_encuestas_custom = models.BooleanField(
        default=False,
        help_text='Básico / Empresarial = NO. Profesional = SÍ. Doc: "plan 3 = encuestas custom máximo 5 preguntas".'
    )
    max_preguntas_encuesta_custom = models.IntegerField(
        default=0,
        help_text='Si tiene_encuestas_custom=True: cantidad máxima de preguntas permitidas por encuesta custom. Doc Profesional = 5.'
    )
    # ======= LANZAMIENTO =======
    es_lanzamiento_gratis = models.BooleanField(
        default=False,
        help_text='Marcar para planes de lanzamiento 365 días gratis (MVP demo). NO aparece en listado de precios normales.'
    )
    dias_prueba_gratis = models.IntegerField(
        default=365,
        help_text='Cantidad de días gratuitos al contratar el plan por primera vez.'
    )
    es_plan_default = models.BooleanField(
        default=False,
        help_text='Plan que se asigna automáticamente durante el onboarding inicial. Solo puede haber uno activo.'
    )
    orden = models.IntegerField(
        default=0,
        help_text='Orden en que aparecen los planes en la UI (menor = primero).'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # ======= FEATURE FLAGS NUEVOS (Planes Excel: Plan1 Solo Google / Plan2 Google+QR CB / Plan3 Full + Benchmark CB) =======
    tiene_analisis_google = models.BooleanField(
        default=True,
        help_text='Análisis rating Google + reseñas Google + evolución histórica Google. Plan1 = True.'
    )
    tiene_benchmark_google = models.BooleanField(
        default=True,
        help_text='Benchmark Google contra competencia (rating, nº opiniones, desempate 3 reglas). Plan1 = True.'
    )
    tiene_notificaciones = models.BooleanField(
        default=True,
        help_text='Notificaciones eventos planes/pagos/benchmark/reseñas/CSAT-NPS. Todos los planes = True.'
    )
    tiene_qr_clientbeat = models.BooleanField(
        default=False,
        help_text='QR encuestas NPS y CSAT por local. Plan1 = False. Plan2 y Plan3 = True.'
    )
    tiene_segmentacion_demografica = models.BooleanField(
        default=False,
        help_text='Segmentación demográfica clientes (edad, género, etc.) desde QR. Plan2 y Plan3 = True.'
    )
    tiene_encuestas_custom_rubro = models.BooleanField(
        default=False,
        help_text='Encuestas personalizadas según dimensiones/atributos del rubro (28 rubros Metodología). Plan2 y Plan3 = True.'
    )
    max_preguntas_adicionales = models.IntegerField(
        default=0,
        help_text='Preguntas adicionales permitidas (fuera del set por rubro). Plan1 = 0, Plan2 = 0, Plan3 = 3.'
    )
    tiene_benchmark_clientbeat = models.BooleanField(
        default=False,
        help_text='BENCHMARK CLIENTBEAT por rubro (comparativa NPS/CSAT/dimensiones con otros CB de misma comuna/región). Plan3 = True.'
    )
    tiene_export_excel = models.BooleanField(
        default=True,
        help_text='Exportar métricas a Excel/CSV. Todos los planes = True.'
    )

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        ordering = ['orden', '-fecha_creacion']

    def __str__(self):
        return self.get_nombre_mostrar()

    def get_nombre_mostrar(self):
        return self.nombre_mostrar or self.nombre

    @classmethod
    def get_plan_default(cls):
        """Devuelve el plan marcado como default activo, o el primer plan activo como fallback."""
        plan = (
            cls.objects.filter(es_plan_default=True, activo=True)
            .order_by('orden', '-fecha_creacion')
            .first()
        )
        if plan is None:
            plan = cls.objects.filter(activo=True).order_by('orden', '-fecha_creacion').first()
        return plan

    def calcular_monto_mensual(self, cantidad_locales: int, cantidad_rubros_online: int = 0) -> int:
        """Calcula costo mensual CLP incluyendo cobros extra escalonados.

        Fórmula (Doc Prompt Tipos de planes):
          - Extra_locales = max(0, cantidad_locales - locales_gratis_incluidos) * costo_local_adicional_clp
          - Extra_rubros  = max(0, cantidad_rubros_online - rubros_gratis_incluidos) * costo_rubro_adicional_clp
          - Total = precio_clp (base) + Extra_locales + Extra_rubros
        """
        base = self.precio_clp or 0
        extra_loc = max(0, int(cantidad_locales) - self.locales_gratis_incluidos) * self.costo_local_adicional_clp
        extra_rub = max(0, int(cantidad_rubros_online) - self.rubros_gratis_incluidos) * self.costo_rubro_adicional_clp
        return base + extra_loc + extra_rub

    def desglose_mensual(self, cantidad_locales: int, cantidad_rubros_online: int = 0) -> dict:
        """Devuelve dict desglose CLP: {base, extra_local, extra_rubro, total, locales_cobrados_extra, rubros_cobrados_extra}."""
        base = self.precio_clp or 0
        locales_cobrados_extra = max(0, int(cantidad_locales) - self.locales_gratis_incluidos)
        rubros_cobrados_extra = max(0, int(cantidad_rubros_online) - self.rubros_gratis_incluidos)
        extra_loc = locales_cobrados_extra * self.costo_local_adicional_clp
        extra_rub = rubros_cobrados_extra * self.costo_rubro_adicional_clp
        return {
            'base_clp': base,
            'local_extra_cantidad': locales_cobrados_extra,
            'local_extra_clp': extra_loc,
            'rubro_extra_cantidad': rubros_cobrados_extra,
            'rubro_extra_clp': extra_rub,
            'total_clp': base + extra_loc + extra_rub,
        }

    def get_precio_display(self):
        """Devuelve precio formateado según moneda configurada."""
        if self.moneda == MonedaChoices.CLP and self.precio_clp is not None:
            return f'${self.precio_clp:,} CLP'.replace(',', '.')
        if self.moneda == MonedaChoices.UF and self.precio_uf is not None:
            return f'UF {self.precio_uf}'
        if self.precio_clp is not None:
            return f'${self.precio_clp:,} CLP'.replace(',', '.')
        return 'Precio por definir'


class Suscripcion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    negocio = models.ForeignKey('businesses.Negocio', on_delete=models.CASCADE, related_name='suscripciones')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='suscripciones')
    estado = models.CharField(max_length=20, choices=EstadoSuscripcionChoices.choices, default=EstadoSuscripcionChoices.PENDIENTE)
    fecha_inicio = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField()
    proximo_ciclo = models.DateTimeField(null=True, blank=True)
    renovacion_automatica = models.BooleanField(default=True)
    cancelada_en = models.DateTimeField(null=True, blank=True)
    motivo_cancelacion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.negocio} - {self.plan.nombre}'


class Pago(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    flow_order_id = models.CharField(max_length=100, unique=True)
    monto = models.IntegerField()
    moneda = models.CharField(max_length=10, default=MonedaChoices.CLP)
    estado = models.CharField(max_length=20, choices=EstadoPagoChoices.choices, default=EstadoPagoChoices.PENDIENTE)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    comprobante_url = models.CharField(max_length=500, null=True, blank=True)
    datos_webhook = models.JSONField(default=dict, blank=True)
    firma_validada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Pago {self.flow_order_id} - {self.estado}'


class RegistroCobranza(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='registros_cobranza')
    tipo = models.CharField(max_length=50, choices=TipoRegistroCobranzaChoices.choices)
    enviado = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    destinatario = models.CharField(max_length=255)
    asunto = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Registro de Cobranza'
        verbose_name_plural = 'Registros de Cobranza'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f'{self.tipo} - {self.suscripcion.id}'
