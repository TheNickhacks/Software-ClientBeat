import uuid
from django.db import models
from django.conf import settings


class Negocio(models.Model):
    class EstadoChoices(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        SUSPENDIDO = 'SUSPENDIDO', 'Suspendido'
        ELIMINADO = 'ELIMINADO', 'Eliminado'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    nombre = models.CharField(
        max_length=255,
        verbose_name='Nombre del negocio'
    )
    rut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='RUT'
    )
    rubro_google = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Rubro (Google)'
    )
    direccion = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Dirección'
    )
    ciudad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ciudad'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    email_contacto = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email de contacto'
    )
    logo = models.ImageField(
        upload_to='negocios/logos/',
        blank=True,
        null=True,
        verbose_name='Logo'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_verificacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de verificación'
    )
    verificado = models.BooleanField(
        default=False,
        verbose_name='Verificado'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
        verbose_name='Estado'
    )
    dueño = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='negocios',
        verbose_name='Dueño'
    )
    comuna = models.ForeignKey(
        'geo.Comuna',
        on_delete=models.SET_NULL,
        related_name='negocios',
        blank=True,
        null=True,
        verbose_name='Comuna'
    )
    rubro = models.ForeignKey(
        'geo.Rubro',
        on_delete=models.SET_NULL,
        related_name='negocios',
        blank=True,
        null=True,
        verbose_name='Rubro del negocio'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )
    onboarding_paso1_completo = models.BooleanField(
        default=False,
        verbose_name='Onboarding Paso 1 Registro completo'
    )
    onboarding_fecha_paso1 = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha Paso 1 (registro)'
    )
    onboarding_paso2_completo = models.BooleanField(
        default=False,
        verbose_name='Onboarding Paso 2 Datos Negocio/Local completo'
    )
    onboarding_fecha_paso2 = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha Paso 2 (datos negocio)'
    )
    onboarding_paso3_completo = models.BooleanField(
        default=False,
        verbose_name='Onboarding Paso 3 Confirmación Plan completo'
    )
    onboarding_fecha_paso3 = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha Paso 3 (confirmación)'
    )

    class Meta:
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre


class MiembroEquipo(models.Model):
    class RolChoices(models.TextChoices):
        DUENO = 'DUENO', 'Dueño'
        USUARIO_EQUIPO = 'USUARIO_EQUIPO', 'Usuario de Equipo'
        GESTOR = 'GESTOR', 'Gestor (solo lectura + gestión encuestas)'

    class EstadoChoices(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        PENDIENTE = 'PENDIENTE', 'Pendiente de invitación'
        DESACTIVADO = 'DESACTIVADO', 'Desactivado'

    class PermisosChoices(models.TextChoices):
        VER_TODO = 'VER_TODO', 'Ver métricas y reseñas'
        GESTIONAR_ENCUESTAS = 'GESTIONAR_ENCUESTAS', 'Crear y gestionar encuestas'
        GESTIONAR_LOCALES = 'GESTIONAR_LOCALES', 'Agregar y editar locales'
        GESTIONAR_EQUIPO = 'GESTIONAR_EQUIPO', 'Invitar y gestionar equipo'
        GESTIONAR_CUENTA = 'GESIONAR_CUENTA', 'Configuración de cuenta y facturación'
        CORREGIR_SENTIMIENTO = 'CORREGIR_SENTIMIENTO', 'Corregir análisis de sentimiento'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='miembros_equipo',
        verbose_name='Negocio'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='membresias_negocios',
        verbose_name='Usuario'
    )
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.USUARIO_EQUIPO,
        verbose_name='Rol en el negocio'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
        verbose_name='Estado'
    )
    permisos = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de permisos específicos (usar PermisosChoices). Si rol=DUEÑO, se ignoran.',
        verbose_name='Permisos específicos'
    )
    fecha_invitacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de invitación'
    )
    fecha_aceptacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de aceptación'
    )
    invitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='miembros_invitados',
        verbose_name='Invitado por'
    )

    class Meta:
        verbose_name = 'Miembro de equipo'
        verbose_name_plural = 'Miembros de equipo'
        unique_together = ('negocio', 'usuario')
        ordering = ['negocio', 'rol', 'fecha_invitacion']

    def __str__(self):
        return f'{self.usuario} en {self.negocio} ({self.get_rol_display()})'

    def tiene_permiso(self, permiso):
        if self.rol == self.RolChoices.DUENO:
            return True
        return permiso in (self.permisos or [])


class Local(models.Model):
    class EstadoChoices(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'
        CERRADO = 'CERRADO', 'Cerrado'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='locales',
        verbose_name='Negocio'
    )
    nombre = models.CharField(
        max_length=255,
        verbose_name='Nombre del local'
    )
    direccion = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Dirección'
    )
    ciudad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ciudad'
    )
    comuna = models.ForeignKey(
        'geo.Comuna',
        on_delete=models.SET_NULL,
        related_name='locales',
        blank=True,
        null=True,
        verbose_name='Comuna'
    )
    latitud = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        blank=True,
        null=True,
        verbose_name='Latitud'
    )
    longitud = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        blank=True,
        null=True,
        verbose_name='Longitud'
    )
    google_place_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Google Place ID'
    )
    horario = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Horario'
    )
    qr_token = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Token QR'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
        verbose_name='Estado'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

    class Meta:
        verbose_name = 'Local'
        verbose_name_plural = 'Locales'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre} ({self.negocio.nombre})'


class Competidor(models.Model):
    class EstadoChoices(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        CERRADO = 'CERRADO', 'Cerrado'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        related_name='competidores',
        verbose_name='Local'
    )
    nombre = models.CharField(
        max_length=255,
        verbose_name='Nombre del competidor'
    )
    google_place_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Google Place ID'
    )
    direccion = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Dirección'
    )
    latitud = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        verbose_name='Latitud'
    )
    longitud = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        verbose_name='Longitud'
    )
    distancia_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name='Distancia (km)'
    )
    rubro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Rubro'
    )
    calificacion_global = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Calificación global'
    )
    numero_opiniones = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Número de opiniones'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
        verbose_name='Estado'
    )
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    class Meta:
        verbose_name = 'Competidor'
        verbose_name_plural = 'Competidores'
        ordering = ['distancia_km']

    def __str__(self):
        return f'{self.nombre} - {self.local.nombre}'


class SnapshotReputacion(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    competidor = models.ForeignKey(
        Competidor,
        on_delete=models.SET_NULL,
        related_name='snapshots',
        blank=True,
        null=True,
        verbose_name='Competidor'
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        related_name='snapshots_local',
        verbose_name='Local'
    )
    fecha_captura = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de captura'
    )
    calificacion = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Calificación'
    )
    opiniones = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Opiniones'
    )
    rank = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Ranking'
    )
    datos = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Datos adicionales'
    )

    class Meta:
        verbose_name = 'Snapshot de reputación'
        verbose_name_plural = 'Snapshots de reputación'
        ordering = ['-fecha_captura']

    def __str__(self):
        return f'Snapshot {self.fecha_captura.strftime("%d/%m/%Y %H:%M")} - {self.local.nombre}'
