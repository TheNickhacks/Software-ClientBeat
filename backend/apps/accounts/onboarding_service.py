from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import login
from django.conf import settings


def get_plan_onboarding(plan_id=None):
    """Retorna el plan a usar para el onboarding (plan seleccionado por ID, plan default o primer plan activo)."""
    from apps.billing.models import Plan
    if plan_id:
        try:
            return Plan.objects.get(id=plan_id, activo=True)
        except Exception:
            pass
    return Plan.get_plan_default()



def completar_suscripcion_default(negocio, plan_id=None):
    """Crea/actualiza la suscripción del negocio usando el Plan por defecto activo o el seleccionado por ID."""
    from apps.billing.models import (
        Plan,
        Suscripcion,
        EstadoSuscripcionChoices,
    )

    plan = get_plan_onboarding(plan_id)

    if plan is None:
        raise RuntimeError(
            'No hay ningún Plan activo configurado en el sistema. '
            'Un Administrador de Soporte debe crear y marcar al menos un plan como "Plan por Defecto".'
        )

    dias_gratis = int(getattr(plan, 'dias_prueba_gratis', 365) or 365)

    ahora = timezone.now()
    suscripcion, creada = Suscripcion.objects.get_or_create(
        negocio=negocio,
        defaults={
            'plan': plan,
            'estado': EstadoSuscripcionChoices.ACTIVA,
            'fecha_inicio': ahora,
            'fecha_vencimiento': ahora + timedelta(days=dias_gratis),
            'proximo_ciclo': ahora + timedelta(days=30),
            'renovacion_automatica': True,
        }
    )
    if not creada:
        suscripcion.plan = plan
        suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
        suscripcion.fecha_vencimiento = max(suscripcion.fecha_vencimiento, ahora + timedelta(days=dias_gratis))
        suscripcion.save()
    return suscripcion


def agregar_dueño_como_miembro_equipo(negocio, usuario, invitado_por=None):
    from apps.businesses.models import MiembroEquipo

    miembro, _ = MiembroEquipo.objects.get_or_create(
        negocio=negocio,
        usuario=usuario,
        defaults={
            'rol': MiembroEquipo.RolChoices.DUENO,
            'estado': MiembroEquipo.EstadoChoices.ACTIVO,
            'permisos': [p[0] for p in MiembroEquipo.PermisosChoices.choices],
            'fecha_aceptacion': timezone.now(),
            'invitado_por': invitado_por or usuario,
        }
    )
    return miembro


def finalizar_onboarding(request, usuario, negocio, local, plan_id=None):
    """Flujo atómico: completa suscripción plan default o seleccionado + login + marca onboarding en sesión."""
    if not plan_id and request and hasattr(request, 'session'):
        plan_id = request.session.get('onboarding_plan_id')
    with transaction.atomic():
        suscripcion = completar_suscripcion_default(negocio, plan_id=plan_id)
        miembro = agregar_dueño_como_miembro_equipo(negocio, usuario)
        marcar_paso3_negocio(negocio)


    usuario.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, usuario)

    request.session['onboarding_completado'] = True
    request.session['negocio_actual_id'] = str(negocio.id)
    request.session['local_actual_id'] = str(local.id)

    return {
        'usuario': usuario,
        'negocio': negocio,
        'local': local,
        'suscripcion': suscripcion,
        'miembro_equipo': miembro,
    }


def marcar_paso1_usuario(usuario):
    """Marca el paso 1 (registro) completo en todos los negocios del usuario (si existen).
    Si el usuario todavía no tiene negocios (caso normal), se marca cuando se crea el negocio en paso 2."""
    from apps.businesses.models import Negocio
    ahora = timezone.now()
    negocios_afectados = Negocio.objects.filter(dueño_id=usuario.id).update(
        onboarding_paso1_completo=True,
        onboarding_fecha_paso1=ahora,
    )
    return negocios_afectados


def marcar_paso2_negocio(negocio, usuario=None):
    """Marca paso 1 (por si no existía) + paso 2 completo en el negocio recién creado (datos + local)."""
    ahora = timezone.now()
    cambios = {
        'onboarding_paso2_completo': True,
        'onboarding_fecha_paso2': ahora,
    }
    # Si paso 1 no estaba marcado (caso normal: negocio acaba de crearse), marcarlo ahora
    if not negocio.onboarding_paso1_completo:
        cambios['onboarding_paso1_completo'] = True
        cambios['onboarding_fecha_paso1'] = ahora
    for campo, valor in cambios.items():
        setattr(negocio, campo, valor)
    negocio.save(update_fields=list(cambios.keys()) + ['fecha_actualizacion'])

    # Asegurarse de que otros negocios del mismo usuario tengan paso1 marcado
    if usuario is not None:
        marcar_paso1_usuario(usuario)
    return negocio


def marcar_paso3_negocio(negocio):
    """Marca paso 3 completo (onboarding finalizado correctamente) en el negocio.
    Garantiza paso 1 y 2 estén marcados."""
    ahora = timezone.now()
    cambios = {
        'onboarding_paso3_completo': True,
        'onboarding_fecha_paso3': ahora,
    }
    if not negocio.onboarding_paso1_completo:
        cambios['onboarding_paso1_completo'] = True
        cambios['onboarding_fecha_paso1'] = ahora
    if not negocio.onboarding_paso2_completo:
        cambios['onboarding_paso2_completo'] = True
        cambios['onboarding_fecha_paso2'] = ahora
    for campo, valor in cambios.items():
        setattr(negocio, campo, valor)
    negocio.save(update_fields=list(cambios.keys()) + ['fecha_actualizacion'])
    return negocio


def onboarding_pendiente(usuario):
    """
    Devuelve True si el usuario aún debe completar el onboarding.
    Considera el onboarding COMPLETO solo si:
    - Es ADMIN_SOPORTE o USUARIO_EQUIPO (nunca tienen onboarding propio)
    - O es DUEÑO y tiene al menos UN Negocio ACTIVO con onboarding_paso3_completo=True
      (o fallback heurístico: suscripción ACTIVA).
    """
    from apps.businesses.models import Negocio
    from apps.billing.models import EstadoSuscripcionChoices
    if usuario.is_authenticated and (getattr(usuario, 'is_admin_soporte', False) or getattr(usuario, 'is_usuario_equipo', False) or getattr(usuario, 'is_staff', False) or getattr(usuario, 'is_superuser', False)):
        return False
    if not usuario.is_authenticated or not hasattr(usuario, 'is_dueno'):
        return True
    if getattr(usuario, 'is_admin_soporte', False) or getattr(usuario, 'is_staff', False) or getattr(usuario, 'is_superuser', False):
        return False

    negocios = Negocio.objects.filter(dueño_id=usuario.id, estado='ACTIVO').prefetch_related('suscripciones')
    if not negocios.exists():
        return True
    for n in negocios:
        # Prioridad 1: flag explícito paso 3 completado
        if getattr(n, 'onboarding_paso3_completo', False):
            return False
        # Fallback heurístico (backward compatible con data previa a FASE 1.6)
        if n.suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).exists():
            return False
    return True


def onboarding_siguiente_paso(usuario):
    """
    Dado un usuario autenticado con onboarding pendiente, devuelve el paso en que debería continuar.
    1) Usa flags explícitos de Negocio (onboarding_paso1_completo, paso2, paso3).
    2) Fallback heurística si flags están NULL (data antigua).
    - Paso 2: cuenta creada (usuario autenticado, paso1=OK, pero sin Negocio O paso2=False)
    - Paso 3: cuenta + negocio/local (paso2=OK) pero paso3=False / sin suscripción ACTIVA
    Devuelve (paso: int, descripcion: str)
    """
    from apps.businesses.models import Negocio, Local
    from apps.billing.models import EstadoSuscripcionChoices
    if not usuario or not getattr(usuario, 'id', None):
        return 1, 'usuario no identificado'
    negocios = Negocio.objects.filter(dueño_id=usuario.id)
    if not negocios.exists():
        return 2, 'cuenta creada pero sin negocio configurado'

    negocio = negocios.first()
    # Flags explicitos
    p1_ok = bool(getattr(negocio, 'onboarding_paso1_completo', False))
    p2_ok = bool(getattr(negocio, 'onboarding_paso2_completo', False))
    p3_ok = bool(getattr(negocio, 'onboarding_paso3_completo', False))
    if not p1_ok:
        # Paso 1 no marcado explícitamente → probable data antigua o re-registro. Volver a paso 2 solo si hay datos.
        if not negocio.locales.exists():
            return 2, 'negocio sin paso1 flag y sin locales creados'
        if not hasattr(negocio, 'suscripciones') or not negocio.suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).exists():
            return 3, 'negocio con locales pero sin suscripcion (fallback sin flags)'
    if p1_ok and not p2_ok:
        return 2, 'paso 1 OK (registro) pero falta completar paso 2 (datos negocio + local)'
    # Paso1 y Paso2 OK → revisar paso3 o suscripción
    if p2_ok and not p3_ok:
        if not negocio.locales.exists():
            return 2, 'paso 2 marcado como OK pero sin locales (rehacer datos del local)'
        if not hasattr(negocio, 'suscripciones') or not negocio.suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).exists():
            return 3, 'paso 2 OK pero falta confirmar plan/suscripción (paso 3)'
    if not negocio.locales.exists():
        return 2, 'negocio sin locales creados'
    if not hasattr(negocio, 'suscripciones') or not negocio.suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).exists():
        return 3, 'negocio y local creados, falta confirmar plan/suscripción'
    return 1, 'onboarding aparentemente completo'
