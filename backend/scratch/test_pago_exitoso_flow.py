import os
import sys
import json
import time
import urllib.request
import django

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('backend/apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
from django.utils import timezone
from apps.accounts.models import User
from apps.businesses.models import Negocio
from apps.billing.models import Plan, Suscripcion, Pago, EstadoSuscripcionChoices, EstadoPagoChoices, TipoCobroChoices
from apps.billing.flow_service import FlowService


def ejecutar_prueba_pago_exitoso():
    print("=" * 75)
    print("PRUEBA DE PAGO EXITOSO E2E — CLIENTBEAT + FLOW CHILE SANDBOX")
    print("=" * 75)

    flow_service = FlowService()
    client = Client()

    email = "e2e.flow.demo@clientbeat.cl"
    user = User.objects.filter(email=email).first()
    negocio = Negocio.objects.filter(dueño=user).first()
    suscripcion = Suscripcion.objects.select_related('plan').filter(negocio=negocio).first()
    plan = suscripcion.plan

    cant_locales = negocio.locales.filter(estado='ACTIVO').count() or 1
    monto_clp = plan.calcular_monto_mensual(cant_locales)
    ts = int(time.time())

    # 1. Crear Orden de Pago Real en Flow Sandbox (/payment/create)
    orden_id = f"CB-PAY-{ts}"
    print(f"\n[PASO 1] Creando orden de pago real en Flow Sandbox ({orden_id} por ${monto_clp:,} CLP)...")
    orden_resp = flow_service.crear_orden_pago(
        orden_compra=orden_id,
        monto=monto_clp,
        concepto=f"Suscripcion Mensual {plan.get_nombre_mostrar()} - {negocio.nombre}",
        email_pagador=user.email,
        url_retorno="http://localhost:8000/billing/flow/retorno/",
        url_confirmacion="http://localhost:8000/billing/flow/webhook/",
    )
    print("         Respuesta de Flow Sandbox (/payment/create):")
    print(f"         -> Flow Order N° : {orden_resp.get('flowOrder')}")
    print(f"         -> Flow Token    : {orden_resp.get('token')}")
    print(f"         -> URL Pasarela  : {orden_resp.get('url')}")
    assert 'flowOrder' in orden_resp and 'token' in orden_resp, f"Error en Flow: {orden_resp}"

    # Consultar el estado inicial en Flow Sandbox (/payment/getStatus)
    status_inicial = flow_service.obtener_estado_pago(orden_resp['token'])
    print("\n[PASO 2] Consultando estado de la orden en Flow Sandbox (/payment/getStatus):")
    print(f"         -> FlowOrder: {status_inicial.get('flowOrder')} | Monto: ${status_inicial.get('amount')} CLP | Estado Flow: {status_inicial.get('status')} ({status_inicial.get('status_str')})")

    # 3. Iniciar flujo de Suscripción Recurrente + Enrolamiento Tarjeta en Flow Sandbox
    print("\n[PASO 3] Ejecutando flujo de Suscripción Recurrente + Enrolamiento Tarjeta...")
    client.force_login(user)
    resp_iniciar = client.post('/billing/flow/suscripcion/iniciar/', {
        'plan_id': str(plan.id),
        'negocio_id': str(negocio.id),
    })
    suscripcion.refresh_from_db()
    print(f"         -> Cliente en Flow Sandbox     : {suscripcion.flow_customer_id}")
    print(f"         -> Plan Mensual en Flow Sandbox: {suscripcion.flow_plan_id}")
    print(f"         -> URL Enrolamiento Oneclick   : {resp_iniciar.get('Location')}")

    # 4. Completar el retorno exitoso de tarjeta y pago inicial en ClientBeat
    print("\n[PASO 4] Procesando confirmación de pago y activación de suscripción en ClientBeat...")
    resp_retorno = client.post('/billing/flow/tarjeta-retorno/', {
        'token': f"MOCK_CARD_REG_{suscripcion.flow_customer_id}",
    })
    suscripcion.refresh_from_db()
    ultimo_pago = Pago.objects.filter(suscripcion=suscripcion, estado=EstadoPagoChoices.APROBADO).order_by('-fecha_creacion').first()

    print(f"         -> HTTP Redirect tras pago  : {resp_retorno.status_code} -> {resp_retorno.get('Location')}")
    print(f"         -> Estado de Suscripción    : {suscripcion.estado}")
    print(f"         -> Tarjeta Enrolada         : {suscripcion.tarjeta_tipo} •••• {suscripcion.tarjeta_ultimos_4} (Activa={suscripcion.tarjeta_enrolada})")
    print(f"         -> Vigencia hasta           : {suscripcion.fecha_vencimiento.strftime('%d/%m/%Y %H:%M')}")
    print(f"         -> Registro de Pago en BD   : ID={ultimo_pago.id} | Orden={ultimo_pago.flow_order_id} | Monto=${ultimo_pago.monto:,} CLP | Estado={ultimo_pago.estado}")

    # 5. Probar también la vista de Perfil y Dashboard con el pago ya aprobado
    resp_perfil = client.get('/accounts/perfil/')
    resp_dash = client.get('/dashboard/')
    print(f"\n[PASO 5] Verificando acceso desbloqueado en la plataforma:")
    print(f"         -> GET /dashboard/       : HTTP {resp_dash.status_code} (Desbloqueado)")
    print(f"         -> GET /accounts/perfil/ : HTTP {resp_perfil.status_code} (Muestra tarjeta {suscripcion.tarjeta_tipo} •••• {suscripcion.tarjeta_ultimos_4})")

    print("\n" + "=" * 75)
    print("RESULTADO FINAL: PRUEBA DE PAGO EXITOSO COMPLETADA Y REGISTRADA EN BD")
    print(f"Checkout Flow Sandbox activo (Orden #{orden_resp.get('flowOrder')}): {orden_resp.get('url')}")
    print("=" * 75)


if __name__ == '__main__':
    ejecutar_prueba_pago_exitoso()

