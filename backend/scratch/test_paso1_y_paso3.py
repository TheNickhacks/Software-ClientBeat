import os
import sys
import json
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
from apps.billing.models import Suscripcion, Pago, EstadoSuscripcionChoices
from apps.billing.flow_service import FlowService
from apps.billing.management.commands.procesar_ciclos_vencidos import ejecutar_barrido_ciclos_vencidos


def test_paso1_y_paso3():
    print("=" * 75)
    print("PROBANDO PASO 1 (BARRIDO DIARIO DUNNING) Y PASO 3 (PRODUCCIÓN & RECIBOS)")
    print("=" * 75)

    user = User.objects.filter(email="e2e.flow.demo@clientbeat.cl").first()
    sus = Suscripcion.objects.filter(negocio__dueño=user).first()
    assert user and sus, "Debe existir la suscripción de prueba"

    # 1. Caso A: Vencida hace 1 día -> Barrido pasa de ACTIVA a EN_GRACIA
    sus.estado = EstadoSuscripcionChoices.ACTIVA
    sus.fecha_vencimiento = timezone.now() - timedelta(days=1)
    sus.dias_gracia = 3
    sus.save(update_fields=['estado', 'fecha_vencimiento', 'dias_gracia'])

    stats_a = ejecutar_barrido_ciclos_vencidos()
    sus.refresh_from_db()
    print(f"[1A] Barrido Día 1 de mora -> Estado: {sus.estado} | Stats: {stats_a}")
    assert sus.estado == EstadoSuscripcionChoices.EN_GRACIA
    assert stats_a['pasadas_a_gracia'] >= 1

    # 2. Caso B: Queda 1 día de gracia (vencida hace 2.5 días) -> Última advertencia
    sus.fecha_vencimiento = timezone.now() - timedelta(days=2, hours=12)
    sus.save(update_fields=['fecha_vencimiento'])

    stats_b = ejecutar_barrido_ciclos_vencidos()
    sus.refresh_from_db()
    print(f"[1B] Barrido Último Día de Gracia (1 día restante) -> Estado: {sus.estado} | Stats: {stats_b}")
    assert stats_b['ultimas_advertencias'] >= 1

    # 3. Caso C: Gracia expirada (vencida hace 4 días) -> Pasa a SUSPENDIDA automáticamente
    sus.fecha_vencimiento = timezone.now() - timedelta(days=4)
    sus.save(update_fields=['fecha_vencimiento'])

    stats_c = ejecutar_barrido_ciclos_vencidos()
    sus.refresh_from_db()
    print(f"[1C] Barrido Día 4 (Gracia expirada) -> Estado: {sus.estado} | Stats: {stats_c}")
    assert sus.estado == EstadoSuscripcionChoices.SUSPENDIDA
    assert stats_c['suspendidas'] >= 1

    # 4. Paso 3A: Validación de Firma Criptográfica HMAC-SHA256 en Webhook
    client = Client()
    flow_service = FlowService()

    # Firma adulterada -> Debe retornar 403
    payload_falso = {
        'event': 'invoice.paid',
        'customerId': sus.flow_customer_id,
        'amount': 50000,
        's': 'firma_falsa_123456',
    }
    resp_403 = client.post('/billing/flow/webhook/', data=json.dumps(payload_falso), content_type='application/json')
    print(f"[3A] Webhook con firma adulterada 's' -> HTTP {resp_403.status_code} (Rechazado correctamente)")
    assert resp_403.status_code == 403

    # Firma HMAC-SHA256 legítima -> Debe retornar 200 y reactivar la suscripción
    payload_real = {
        'event': 'invoice.paid',
        'customerId': sus.flow_customer_id,
        'invoiceId': 'INV-SIGNED-OK-001',
        'amount': 50000,
    }
    payload_real['s'] = flow_service.firmar_parametros(payload_real)
    resp_200 = client.post('/billing/flow/webhook/', data=json.dumps(payload_real), content_type='application/json')
    sus.refresh_from_db()
    print(f"[3B] Webhook con firma HMAC-SHA256 legítima -> HTTP {resp_200.status_code} | Suscripción: {sus.estado}")
    assert resp_200.status_code == 200
    assert sus.estado == EstadoSuscripcionChoices.ACTIVA

    # 5. Paso 3B: Comprobante de Pago Imprimible / PDF
    client.force_login(user)
    pago = Pago.objects.filter(suscripcion=sus).order_by('-fecha_creacion').first()
    resp_comp = client.get(f'/billing/comprobante/{pago.id}/')
    html = resp_comp.content.decode('utf-8')
    print(f"[3C] GET /billing/comprobante/{pago.id}/ -> HTTP {resp_comp.status_code} | Contiene orden {pago.flow_order_id}: {pago.flow_order_id in html}")
    assert resp_comp.status_code == 200
    assert pago.flow_order_id in html

    print("\n" + "=" * 75)
    print("[OK] PASO 1 Y PASO 3 VERIFICADOS AL 100%.")
    print("=" * 75)


if __name__ == '__main__':
    test_paso1_y_paso3()

