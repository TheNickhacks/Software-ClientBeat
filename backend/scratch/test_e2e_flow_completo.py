import os
import sys
import json
import time
import django
from datetime import timedelta

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
from apps.businesses.models import Negocio, Local
from apps.billing.models import Plan, Suscripcion, Pago, EstadoSuscripcionChoices, TipoCobroChoices
from apps.billing.flow_service import FlowService


def run_e2e_flow_test():
    print("=" * 72)
    print("EJECUTANDO FLUJO E2E COMPLETO: CLIENTBEAT + FLOW SANDBOX REAL")
    print("=" * 72)

    client = Client()
    flow_service = FlowService()
    print(f"[1] Flow Environment: {flow_service.environment} | Base URL: {flow_service.base_url} | Mock: {flow_service.is_mock}")
    assert not flow_service.is_mock, "Las credenciales de Flow Sandbox deben estar activas"

    # Crear o recuperar usuario y negocio de prueba
    ts = int(time.time())
    email = "e2e.flow.demo@clientbeat.cl"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': f'e2e_flow_{ts}',
            'first_name': 'Nicolás',
            'last_name': 'Navarrete (Flow E2E)',
            'rol': User.RolChoices.DUENO,
            'es_mayor_18': True,
        }
    )
    user.set_password('ClientBeat2026!')
    user.save()

    plan = Plan.objects.filter(activo=True).first()
    if not plan:
        plan = Plan.objects.create(
            nombre='EMPRESARIAL',
            precio_clp=25000,
            locales_gratis_incluidos=1,
            costo_local_adicional_clp=10000,
            activo=True,
            es_plan_default=True,
        )

    negocio, _ = Negocio.objects.get_or_create(
        dueño=user,
        defaults={
            'nombre': 'Café & Bistro Flow Demo',
            'direccion': 'Av. Providencia 1234',
            'ciudad': 'Santiago',
            'estado': 'ACTIVO',
            'onboarding_paso1_completo': True,
            'onboarding_paso2_completo': True,
            'onboarding_paso3_completo': True,
        }
    )
    Local.objects.get_or_create(
        negocio=negocio,
        nombre='Sucursal Casa Matriz',
        defaults={
            'direccion': 'Av. Providencia 1234',
            'ciudad': 'Santiago',
            'estado': 'ACTIVO',
            'qr_token': f'CB-FLOW-{str(ts)[-6:]}',
        }
    )

    # Configurar suscripción inicialmente SUSPENDIDA para probar Hard Paywall
    suscripcion, _ = Suscripcion.objects.update_or_create(
        negocio=negocio,
        defaults={
            'plan': plan,
            'estado': EstadoSuscripcionChoices.SUSPENDIDA,
            'fecha_inicio': timezone.now() - timedelta(days=35),
            'fecha_vencimiento': timezone.now() - timedelta(days=5),
            'dias_gracia': 3,
        }
    )

    client.force_login(user)

    # PASO 1: Probar Hard Paywall (Middleware bloquea /dashboard/ y redirige a /billing/bloqueado/)
    resp_dash = client.get('/dashboard/')
    print(f"[2] Hard Paywall en /dashboard/ con cuenta SUSPENDIDA -> HTTP {resp_dash.status_code} -> {resp_dash.get('Location')}")
    assert resp_dash.status_code == 302 and '/billing/bloqueado/' in resp_dash.get('Location', '')

    resp_bloq = client.get('/billing/bloqueado/')
    print(f"[3] Vista /billing/bloqueado/ renderizada -> HTTP {resp_bloq.status_code}")
    assert resp_bloq.status_code == 200

    # PASO 2: Iniciar Suscripción en Flow Sandbox Real (POST /billing/flow/suscripcion/iniciar/)
    resp_iniciar = client.post('/billing/flow/suscripcion/iniciar/', {
        'plan_id': str(plan.id),
        'negocio_id': str(negocio.id),
    })
    flow_redirect_url = resp_iniciar.get('Location', '')
    print(f"[4] POST /billing/flow/suscripcion/iniciar/ -> HTTP {resp_iniciar.status_code}")
    print(f"    URL Redirección Flow Sandbox: {flow_redirect_url}")
    assert resp_iniciar.status_code == 302 and 'sandbox.flow.cl' in flow_redirect_url

    suscripcion.refresh_from_db()
    print(f"    Cliente Flow ID guardado en BD: {suscripcion.flow_customer_id}")
    print(f"    Plan Flow ID sincronizado en BD: {suscripcion.flow_plan_id}")
    assert suscripcion.flow_customer_id and suscripcion.flow_customer_id.startswith('cus_')

    # PASO 3: Simular Retorno Exitoso de Enrolamiento de Tarjeta Oneclick (POST cross-site desde Flow)
    resp_retorno = client.post('/billing/flow/tarjeta-retorno/', {
        'token': f'MOCK_CARD_REG_{suscripcion.flow_customer_id}',
    })
    suscripcion.refresh_from_db()
    print(f"[5] POST /billing/flow/tarjeta-retorno/ -> HTTP {resp_retorno.status_code} -> {resp_retorno.get('Location')}")
    print(f"    Estado Suscripción tras retorno: {suscripcion.estado} | Tarjeta: {suscripcion.tarjeta_tipo} **** {suscripcion.tarjeta_ultimos_4}")
    assert suscripcion.estado == EstadoSuscripcionChoices.ACTIVA
    assert suscripcion.tarjeta_enrolada is True

    # Verificar que ahora /dashboard/ NO está bloqueado por SubscriptionRequiredMiddleware
    resp_dash_ok = client.get('/dashboard/')
    print(f"[6] Acceso a /dashboard/ con suscripción ACTIVA -> HTTP {resp_dash_ok.status_code}")
    assert resp_dash_ok.status_code == 200

    # PASO 4: Probar Webhook Mes 2 - Cobro Exitoso (invoice.paid)
    resp_wh_paid = client.post(
        '/billing/flow/webhook/',
        data=json.dumps({
            'event': 'invoice.paid',
            'customerId': suscripcion.flow_customer_id,
            'subscriptionId': suscripcion.flow_subscription_id,
            'invoiceId': f'INV-{ts}',
            'amount': 25000,
        }),
        content_type='application/json'
    )
    print(f"[7] Webhook invoice.paid (Mes 2) -> HTTP {resp_wh_paid.status_code} | Resp: {resp_wh_paid.json()}")
    assert resp_wh_paid.status_code == 200

    # PASO 5: Probar Webhook Mes 2 - Fallo de Cobro Dentro de los 3 Días de Gracia (invoice.payment_failed)
    suscripcion.fecha_vencimiento = timezone.now() - timedelta(days=1)
    suscripcion.save(update_fields=['fecha_vencimiento'])

    resp_wh_fail1 = client.post(
        '/billing/flow/webhook/',
        data=json.dumps({
            'event': 'invoice.payment_failed',
            'customerId': suscripcion.flow_customer_id,
            'subscriptionId': suscripcion.flow_subscription_id,
        }),
        content_type='application/json'
    )
    suscripcion.refresh_from_db()
    print(f"[8] Webhook invoice.payment_failed (Día 1 de mora -> 3 días de gracia):")
    print(f"    Estado: {suscripcion.estado} | En Gracia: {suscripcion.en_periodo_gracia()} | Días restantes gracia: {suscripcion.dias_restantes_gracia()} | Bloqueada: {suscripcion.esta_bloqueada()}")
    assert suscripcion.estado == EstadoSuscripcionChoices.EN_GRACIA
    assert not suscripcion.esta_bloqueada()

    # PASO 6: Probar Webhook Mes 2 - Expiración de los 3 Días de Gracia (Día 4 de mora -> SUSPENDIDA y Bloqueo)
    suscripcion.fecha_vencimiento = timezone.now() - timedelta(days=4)
    suscripcion.save(update_fields=['fecha_vencimiento'])

    resp_wh_fail2 = client.post(
        '/billing/flow/webhook/',
        data=json.dumps({
            'event': 'invoice.payment_failed',
            'customerId': suscripcion.flow_customer_id,
            'subscriptionId': suscripcion.flow_subscription_id,
        }),
        content_type='application/json'
    )
    suscripcion.refresh_from_db()
    print(f"[9] Webhook invoice.payment_failed (Día 4 de mora -> Gracia expirada):")
    print(f"    Estado: {suscripcion.estado} | Bloqueada: {suscripcion.esta_bloqueada()}")
    assert suscripcion.estado == EstadoSuscripcionChoices.SUSPENDIDA
    assert suscripcion.esta_bloqueada()

    # Dejar la suscripción ACTIVA y generar un link fresco de Flow Sandbox para abrir en Chrome
    suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
    suscripcion.fecha_vencimiento = timezone.now() + timedelta(days=30)
    suscripcion.save(update_fields=['estado', 'fecha_vencimiento'])

    reg_live = flow_service.iniciar_registro_tarjeta(
        customer_id=suscripcion.flow_customer_id,
        url_retorno="http://localhost:8000/billing/flow/tarjeta-retorno/"
    )
    print("\n" + "=" * 72)
    print("[OK] FLUJO E2E VALIDADO AL 100%.")
    print(f"URL VIVA DE ENROLAMIENTO FLOW SANDBOX: {reg_live.get('url')}")
    print("=" * 72)


if __name__ == '__main__':
    run_e2e_flow_test()

