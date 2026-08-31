import os
import sys
import secrets

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import Client
from apps.geo.models import Region, Provincia, Comuna, Rubro

client = Client()

test_email = f"testuser_{secrets.token_hex(4)}@example.com"
print(f"Testing full wizard registration for new email: {test_email}")

# --- PASO 1 ---
print("\n--- Testing Paso 1 POST ---")
p1_data = {
    'first_name': 'Juan',
    'last_name': 'Pérez',
    'email': test_email,
    'telefono': '+56912345678',
    'password1': 'Password123!',
    'password2': 'Password123!',
    'es_mayor_18': 'on',
    'acepto_terminos': 'on',
    'paso': '1',
}

res1 = client.post('/accounts/register/?paso=1', p1_data, follow=True)
print(f"Paso 1 Response Status: {res1.status_code}")
print(f"Redirect chain: {res1.redirect_chain}")
if res1.status_code != 200:
    print("Content:", res1.content.decode('utf-8')[:1000])

# Check session
print(f"Session user_id: {client.session.get('onboarding_user_id')}")

# --- PASO 2 ---
print("\n--- Testing Paso 2 POST ---")
reg = Region.objects.filter(activo=True).first()
prov = reg.provincias.first() if reg else None
com = prov.comunas.first() if prov else None
rubro = Rubro.objects.first()

p2_data = {
    'paso': '2',
    'neg-nombre': 'Mi Negocio Test SpA',
    'neg-razon_social': 'Mi Negocio Test SpA',
    'neg-rut': '76.999.888-7',
    'neg-rango_empleados': 'R1',
    'neg-direccion': 'Av Providencia 1234',
    'neg-region': reg.id,
    'neg-provincia': prov.id,
    'neg-comuna': com.id,
    'neg-rubro': rubro.id,
    'neg-acepto_politica_datos_check': 'on',
    'loc-nombre': 'Local Matriz',
    'loc-direccion': 'Av Providencia 1234',
    'loc-comuna': com.id,
    'loc-usar_datos_negocio': 'on',
}

res2 = client.post('/accounts/onboarding/?paso=2', p2_data, follow=True)
print(f"Paso 2 Response Status: {res2.status_code}")
print(f"Redirect chain: {res2.redirect_chain}")
if res2.status_code != 200:
    print("Content:", res2.content.decode('utf-8')[:1000])

print(f"Session negocio_id: {client.session.get('onboarding_negocio_id')}")
print(f"Session local_id: {client.session.get('onboarding_local_id')}")

# --- PASO 3 ---
print("\n--- Testing Paso 3 POST ---")
p3_data = {
    'paso': '3',
    'aceptar_plan': '1',
}

res3 = client.post('/accounts/onboarding/?paso=3', p3_data, follow=True)
print(f"Paso 3 Response Status: {res3.status_code}")
print(f"Redirect chain: {res3.redirect_chain}")
if res3.status_code != 200:
    print("Content:", res3.content.decode('utf-8')[:1000])

print("\n--- Full Wizard Test Finished ---")
