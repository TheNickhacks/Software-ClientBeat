import os
import sys
import time
import secrets

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import Client
from apps.geo.models import Region, Provincia, Comuna, Rubro

client = Client()

test_email = f"speedtest_{secrets.token_hex(4)}@example.com"
test_password = "Password123!"

print(f"=== TESTING REGISTRATION & PERFORMANCE ===")
print(f"Test Email: {test_email}")

# --- 1. PASO 1 ---
t0 = time.time()
p1_data = {
    'first_name': 'Carlos',
    'last_name': 'Valenzuela',
    'email': test_email,
    'telefono': '+56987654321',
    'password1': test_password,
    'password2': test_password,
    'es_mayor_18': 'on',
    'acepto_terminos': 'on',
    'paso': '1',
}

res1 = client.post('/accounts/register/?paso=1', p1_data, follow=True)
t_p1 = time.time() - t0
print(f"Paso 1 POST Time: {t_p1:.3f} seconds | Status: {res1.status_code}")
print(f"Redirect Chain: {res1.redirect_chain}")
assert res1.status_code == 200, "Paso 1 failed"

# --- 2. PASO 1 RE-SUBMISSION (IDEMPOTENCY TEST) ---
t0 = time.time()
res1_retry = client.post('/accounts/register/?paso=1', p1_data, follow=True)
t_p1_retry = time.time() - t0
print(f"Paso 1 RE-POST Time: {t_p1_retry:.3f} seconds | Status: {res1_retry.status_code}")
print(f"Re-POST Redirect Chain: {res1_retry.redirect_chain}")
assert res1_retry.status_code == 200, "Paso 1 re-post failed"

# --- 3. PASO 2 ---
reg = Region.objects.filter(activo=True).first()
prov = reg.provincias.first() if reg else None
com = prov.comunas.first() if prov else None
rubro = Rubro.objects.first()

p2_data = {
    'paso': '2',
    'neg-nombre': 'Speed Test Negocio SpA',
    'neg-razon_social': 'Speed Test Negocio SpA',
    'neg-rut': '76.111.222-3',
    'neg-rango_empleados': 'R1',
    'neg-direccion': 'Av Providencia 555',
    'neg-region': reg.id,
    'neg-provincia': prov.id,
    'neg-comuna': com.id,
    'neg-rubro': rubro.id,
    'neg-acepto_politica_datos_check': 'on',
    'loc-nombre': 'Matriz Providencia',
    'loc-direccion': 'Av Providencia 555',
    'loc-comuna': com.id,
    'loc-usar_datos_negocio': 'on',
}

t0 = time.time()
res2 = client.post('/accounts/onboarding/?paso=2', p2_data, follow=True)
t_p2 = time.time() - t0
print(f"Paso 2 POST Time: {t_p2:.3f} seconds | Status: {res2.status_code}")
assert res2.status_code == 200, "Paso 2 failed"

# --- 4. PASO 3 ---
p3_data = {
    'paso': '3',
    'aceptar_plan': '1',
}

t0 = time.time()
res3 = client.post('/accounts/onboarding/?paso=3', p3_data, follow=True)
t_p3 = time.time() - t0
print(f"Paso 3 POST Time: {t_p3:.3f} seconds | Status: {res3.status_code}")
print(f"Final Redirect: {res3.redirect_chain}")
assert res3.status_code == 200, "Paso 3 failed"

# --- 5. DASHBOARD TAB PERFORMANCE ---
print("\n--- DASHBOARD TAB PERFORMANCE TESTS ---")
for tab in ['resumen', 'encuestas', 'google', 'analisis', 'benchmark']:
    t0 = time.time()
    res_tab = client.get(f'/dashboard/?tab={tab}')
    t_tab = time.time() - t0
    print(f"Tab '{tab}' GET Time: {t_tab:.3f} seconds | Status: {res_tab.status_code}")
    assert res_tab.status_code == 200, f"Tab {tab} failed"

print("\n=== ALL SPEED & PERFORMANCE TESTS PASSED SUCCESSFULLY! ===")
