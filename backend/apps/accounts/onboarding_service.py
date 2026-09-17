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
    """Crea/actualiza la suscripción del negocio usando el Plan por defecto o seleccionado.

    ⚠️ Regla suscripción: NUEVAS suscripciones post-onboarding = PENDIENTE.
    Solo Admin Soporte la marca ACTIVA después de confirmar el pago (o si es plan
    lanzamiento gratuito default con >=30 días de prueba).
    """
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
    es_lanzamiento_gratis = bool(getattr(plan, 'es_plan_default', False)) and dias_gratis >= 30

    ahora = timezone.now()
    suscripcion, creada = Suscripcion.objects.get_or_create(
        negocio=negocio,
        defaults={
            'plan': plan,
            # ================= SUSCRIPCIÓN PENDIENTE POST-ONBOARDING =================
            # No activamos el plan hasta que Admin Soporte lo confirme.
            'estado': EstadoSuscripcionChoices.ACTIVA if es_lanzamiento_gratis else EstadoSuscripcionChoices.PENDIENTE,
            'fecha_inicio': ahora,
            'fecha_vencimiento': ahora + timedelta(days=dias_gratis),
            'proximo_ciclo': ahora + timedelta(days=30),
            'renovacion_automatica': True,
        }
    )
    if not creada:
        suscripcion.plan = plan
        # ⚠️ No cambiamos el estado arbitrariamente de una suscripción ya existente
        # (lo maneja Admin Soporte desde el panel).
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


_ONBOARDING_CACHE_TTL_SEGUNDOS = 300  # 5 min cache en session para evitar martillar NeonDB


def _cache_key(usuario):
    uid = getattr(usuario, 'pk', None) or getattr(usuario, 'id', None) or str(usuario)
    return f'ob_cache_{uid}'


def _cache_leer(session, usuario):
    if session is None:
        return None
    try:
        data = session.get(_cache_key(usuario))
        if not data or not isinstance(data, dict):
            return None
        import time as _time
        ts = data.get('_ts', 0)
        if _time.time() - ts > _ONBOARDING_CACHE_TTL_SEGUNDOS:
            return None
        return data
    except Exception:
        return None


def _cache_guardar(session, usuario, data):
    if session is None:
        return
    import time as _time
    data = dict(data)
    data['_ts'] = _time.time()
    session[_cache_key(usuario)] = data
    try:
        session.modified = True
    except Exception:
        pass


def onboarding_cache_invalidar(session, usuario):
    """Llama esto SIEMPRE que modifiques algún flag de onboarding en BD."""
    if session is None:
        return
    try:
        session.pop(_cache_key(usuario), None)
        session.modified = True
    except Exception:
        pass


def onboarding_pendiente(usuario, session=None):
    """
    Devuelve True si el usuario aún debe completar el onboarding.
    🏁 OPTIMIZACIÓN DEFINITIVA:
    - Cache TTL 5min en session (si se pasa) → 0 queries NeonDB.
    - Si no hay cache → 1 SOLA query SQL (sin prefetch_related, sin loops).
    - Fallback heurístico: suscripción ACTIVA O PENDIENTE = onboarding ya pasó.
    """
    from apps.businesses.models import Negocio
    from apps.billing.models import EstadoSuscripcionChoices, Suscripcion
    from django.db.models import Exists, OuterRef, Q

    if session is not None:
        cached = _cache_leer(session, usuario)
        if cached is not None:
            return bool(cached.get('pendiente', True))

    if not usuario.is_authenticated:
        return True
    rol_global = getattr(usuario, 'rol', None)
    if usuario.is_superuser or rol_global in ('ADMIN_SOPORTE', 'USUARIO_EQUIPO'):
        if session is not None:
            _cache_guardar(session, usuario, {'pendiente': False, 'paso': 4, 'explicacion': 'Rol sin onboarding propio'})
        return False
    if rol_global != 'DUENO':
        return True

    # 🏁 1 SOLA QUERY con EXISTS + Subquery
    condicion_listo = (
        Q(onboarding_paso3_completo=True)
        | Q(
            Exists(
                Suscripcion.objects.filter(
                    negocio=OuterRef('pk'),
                    estado__in=(EstadoSuscripcionChoices.ACTIVA, EstadoSuscripcionChoices.PENDIENTE),
                )
            )
        )
    )
    tiene_negocio_listo = (
        Negocio.objects
        .filter(dueño_id=usuario.id, estado='ACTIVO')
        .filter(condicion_listo)
        .exists()
    )
    pendiente = not tiene_negocio_listo

    if session is not None:
        _cache_guardar(session, usuario, {
            'pendiente': pendiente,
            'paso': (1 if pendiente else 4),
            'explicacion': ('Negocio configurado y suscripcion OK' if not pendiente else 'Falta completar onboarding')
        })
    return pendiente


def onboarding_siguiente_paso(usuario, session=None):
    """
    Devuelve (paso:int, explicacion:str).
    Paso 1 = solo email/registro | Paso 2 = datos Negocio + Local | Paso 3 = plan | Paso 4 = TODO LISTO.
    🏁 Con cache session. 1 sola query (solo fields mínimos).
    """
    from apps.businesses.models import Negocio

    if session is not None:
        cached = _cache_leer(session, usuario)
        if cached is not None:
            return (int(cached.get('paso', 1)), cached.get('explicacion', ''))

    if not usuario.is_authenticated:
        return (1, 'Sin autenticar')
    rol_global = getattr(usuario, 'rol', None)
    if usuario.is_superuser or rol_global in ('ADMIN_SOPORTE', 'USUARIO_EQUIPO'):
        if session is not None:
            _cache_guardar(session, usuario, {'pendiente': False, 'paso': 4, 'explicacion': 'Rol salta onboarding'})
        return (4, 'Rol salta onboarding')
    if rol_global != 'DUENO':
        return (1, 'Rol requiere onboarding')

    # 🏁 1 sola query, solo fields que importan
    n = (
        Negocio.objects
        .filter(dueño_id=usuario.id, estado='ACTIVO')
        .only('onboarding_paso1_completo', 'onboarding_paso2_completo', 'onboarding_paso3_completo', 'id')
        .order_by('-fecha_creacion')
        .first()
    )
    paso = 1
    explicacion = 'Solo cuenta creada — completa datos negocio (Paso 2)'
    if n is not None:
        p1 = bool(getattr(n, 'onboarding_paso1_completo', False))
        p2 = bool(getattr(n, 'onboarding_paso2_completo', False))
        p3 = bool(getattr(n, 'onboarding_paso3_completo', False))
        if p3:
            paso = 4
            explicacion = 'Onboarding completo'
        elif p2:
            paso = 3
            explicacion = 'Falta confirmar plan (Paso 3)'
        elif p1:
            paso = 2
            explicacion = 'Falta datos Negocio + Local (Paso 2)'
        else:
            paso = 2
            explicacion = 'Negocio creado pero sin flags onboarding (Paso 2)'

    pendiente = (paso <= 3)
    if session is not None:
        _cache_guardar(session, usuario, {'pendiente': pendiente, 'paso': paso, 'explicacion': explicacion})
    return (paso, explicacion)
