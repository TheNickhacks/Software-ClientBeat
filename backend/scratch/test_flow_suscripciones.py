import os
import sys
import django
from datetime import timedelta

# Configuración del entorno Django
sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('backend/apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from apps.billing.flow_service import FlowService
from apps.billing.models import Plan, Suscripcion, Pago, EstadoSuscripcionChoices, TipoCobroChoices
from apps.businesses.models import Negocio
from apps.accounts.models import User

def test_flow():
    print("=" * 60)
    print("PROBANDO MOTOR DE SUSCRIPCIONES FLOW CHILE (SANDBOX REAL)")
    print("=" * 60)

    service = FlowService()
    print(f"1. Entorno: {service.environment} | Is Mock: {service.is_mock} | URL: {service.base_url}")

    import time
    ext_id = f"cb-test-{int(time.time())}"
    email_test = f"demo.{int(time.time())}@clientbeat.cl"

    # Test 1: Crear Cliente
    cliente = service.crear_cliente("Negocio Demo ClientBeat SpA", email_test, ext_id)
    print("2. Respuesta /customer/create:", cliente)

    if 'customerId' in cliente:
        # Test 2: Iniciar Enrolamiento Tarjeta
        reg = service.iniciar_registro_tarjeta(cliente['customerId'], "http://localhost:8000/billing/flow/tarjeta-retorno/")
        print("3. Respuesta /customer/register:", reg)

        # Test 3: Sincronizar Plan
        plan_code = "CB-EMPRESARIAL-1LOC-25000"
        plan_resp = service.sincronizar_o_crear_plan(plan_code, "Plan Empresarial (1 loc)", 25000)
        print("4. Respuesta /plans/create o /plans/get:", plan_resp)
    else:
        print("   [!] Nota sobre /customer/create:", cliente)

    # Test 7: Lógica de Bloqueo y Dunning de Suscripcion
    print("\n" + "=" * 60)
    print("PROBANDO LÓGICA DE BLOQUEO Y GRACIA (3 DÍAS)")
    print("=" * 60)

    plan = Plan.objects.first()
    if not plan:
        plan = Plan.objects.create(nombre="TEST_PLAN", precio_clp=25000)

    negocio = Negocio.objects.first()

    # Caso A: Activa -> NO bloqueada
    s_activa = Suscripcion(
        negocio=negocio,
        plan=plan,
        estado=EstadoSuscripcionChoices.ACTIVA,
        fecha_inicio=timezone.now(),
        fecha_vencimiento=timezone.now() + timedelta(days=30),
        dias_gracia=3
    )
    print("Caso A (Activa):", "Bloqueada =", s_activa.esta_bloqueada())
    assert not s_activa.esta_bloqueada()

    # Caso B: Suspendida por impago -> Bloqueada
    s_suspendida = Suscripcion(
        negocio=negocio,
        plan=plan,
        estado=EstadoSuscripcionChoices.SUSPENDIDA,
        fecha_inicio=timezone.now() - timedelta(days=35),
        fecha_vencimiento=timezone.now() - timedelta(days=5),
        dias_gracia=3
    )
    print("Caso B (Suspendida):", "Bloqueada =", s_suspendida.esta_bloqueada())
    assert s_suspendida.esta_bloqueada()

    # Caso C: Vencida hace 1 día (dentro de los 3 días de gracia) -> NO bloqueada, en gracia = True
    s_gracia = Suscripcion(
        negocio=negocio,
        plan=plan,
        estado=EstadoSuscripcionChoices.VENCIDA,
        fecha_inicio=timezone.now() - timedelta(days=31),
        fecha_vencimiento=timezone.now() - timedelta(days=1),
        dias_gracia=3
    )
    print("Caso C (Vencida hace 1 día):", "Bloqueada =", s_gracia.esta_bloqueada(), "| En gracia =", s_gracia.en_periodo_gracia(), "| Días restantes =", s_gracia.dias_restantes_gracia())
    assert not s_gracia.esta_bloqueada()
    assert s_gracia.en_periodo_gracia()
    assert s_gracia.dias_restantes_gracia() >= 1

    # Caso D: Vencida hace 5 días (fuera de los 3 días de gracia) -> Bloqueada
    s_expirada = Suscripcion(
        negocio=negocio,
        plan=plan,
        estado=EstadoSuscripcionChoices.VENCIDA,
        fecha_inicio=timezone.now() - timedelta(days=35),
        fecha_vencimiento=timezone.now() - timedelta(days=5),
        dias_gracia=3
    )
    print("Caso D (Vencida hace 5 días):", "Bloqueada =", s_expirada.esta_bloqueada(), "| En gracia =", s_expirada.en_periodo_gracia())
    assert s_expirada.esta_bloqueada()
    assert not s_expirada.en_periodo_gracia()

    print("\n[OK] TODOS LOS TESTS DE INTEGRACION DE SUSCRIPCIONES FLOW PASARON SATISFACTORIAMENTE.")

if __name__ == '__main__':
    test_flow()
