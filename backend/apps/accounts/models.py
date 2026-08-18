import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class RolChoices(models.TextChoices):
        ADMIN_SOPORTE = 'ADMIN_SOPORTE', 'Admin Soporte ClienBeat'
        DUENO = 'DUENO', 'Dueño de Negocio'
        USUARIO_EQUIPO = 'USUARIO_EQUIPO', 'Usuario de Equipo'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Correo electrónico'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    acepto_terminos = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de aceptación de términos'
    )
    es_mayor_18 = models.BooleanField(
        default=False,
        verbose_name='Es mayor de 18 años'
    )
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.USUARIO_EQUIPO,
        verbose_name='Rol global'
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actividad'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.get_full_name() or self.email} ({self.get_rol_display()})'

    @property
    def is_admin_soporte(self):
        return self.rol == self.RolChoices.ADMIN_SOPORTE or self.is_superuser

    @property
    def is_dueno(self):
        return self.rol == self.RolChoices.DUENO or self.is_admin_soporte

    @property
    def is_usuario_equipo(self):
        return self.rol == self.RolChoices.USUARIO_EQUIPO

    def pertenece_a_negocio(self, negocio_id):
        from apps.businesses.models import MiembroEquipo, Negocio
        if self.is_admin_soporte:
            return True
        if not negocio_id:
            return False
        try:
            negocio = Negocio.objects.get(id=negocio_id)
            if negocio.dueño_id == self.id:
                return True
        except Negocio.DoesNotExist:
            return False
        return MiembroEquipo.objects.filter(
            negocio_id=negocio_id,
            usuario_id=self.id,
            estado=MiembroEquipo.EstadoChoices.ACTIVO
        ).exists()

    def negocios_permitidos_qs(self):
        from apps.businesses.models import MiembroEquipo, Negocio
        if self.is_admin_soporte:
            return Negocio.objects.all()
        if self.rol == self.RolChoices.DUENO:
            return Negocio.objects.filter(dueño_id=self.id)
        return Negocio.objects.filter(
            id__in=MiembroEquipo.objects.filter(
                usuario_id=self.id,
                estado=MiembroEquipo.EstadoChoices.ACTIVO
            ).values_list('negocio_id', flat=True)
        )

    def rol_en_negocio(self, negocio_id):
        from apps.businesses.models import MiembroEquipo, Negocio
        if self.is_admin_soporte:
            return 'ADMIN_SOPORTE'
        try:
            negocio = Negocio.objects.get(id=negocio_id)
            if negocio.dueño_id == self.id:
                return 'DUENO'
        except Negocio.DoesNotExist:
            return None
        try:
            miembro = MiembroEquipo.objects.get(
                negocio_id=negocio_id,
                usuario_id=self.id,
                estado=MiembroEquipo.EstadoChoices.ACTIVO
            )
            return miembro.rol
        except MiembroEquipo.DoesNotExist:
            return None

    def puede_gestionar_cuenta(self, negocio_id):
        rol = self.rol_en_negocio(negocio_id)
        return rol in ('ADMIN_SOPORTE', 'DUENO')

    def puede_ver_indicadores(self, negocio_id):
        rol = self.rol_en_negocio(negocio_id)
        return rol in ('ADMIN_SOPORTE', 'DUENO', 'USUARIO_EQUIPO')
