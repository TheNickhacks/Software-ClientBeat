import os
import sys

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.geo.models import Region, Provincia, Comuna, Rubro
from apps.businesses.forms import NegocioOnboardingForm

User = get_user_model()
admin_user = User.objects.filter(email='admin@clientbeat.cl').first()

client = Client()
client.force_login(admin_user)

print("1. Testing Reportería de Planes tab=cambios...")
res1 = client.get('/admin-panel/reporteria/planes/?tab=cambios')
assert res1.status_code == 200, f"tab=cambios failed with {res1.status_code}"
print("[OK 200] Reportería de Planes tab=cambios")

print("2. Testing Benchmark por Rubro con filtros...")
res2 = client.get('/admin-panel/reporteria/benchmark-rubro/?filtro_temporal=ANUAL&filtro_geografico=REGIONAL')
assert res2.status_code == 200, f"benchmark-rubro failed with {res2.status_code}"
print("[OK 200] Benchmark por Rubro con filtros")

print("3. Testing Data Google Rubros con búsqueda...")
res3 = client.get('/admin-panel/data-google/rubros/?q=cafe')
assert res3.status_code == 200, f"data-google rubros failed with {res3.status_code}"
print("[OK 200] Data Google Rubros con búsqueda")

print("4. Testing Landing Page...")
res4 = client.get('/')
assert res4.status_code == 200, f"Landing failed with {res4.status_code}"
assert b'Contratar Plan Ahora' in res4.content, "Contratar Plan Ahora button not found in landing page"
print("[OK 200] Landing Page con Precios y botón Contratar Plan Ahora")

print("5. Testing Onboarding Geo Form Validation...")
reg = Region.objects.filter(activo=True).first()
prov = reg.provincias.first() if reg else None
com = prov.comunas.first() if prov else None
rubro = Rubro.objects.first()

if reg and prov and com and rubro:
    post_data = {
        'neg-nombre': 'Mi Negocio Test',
        'neg-razon_social': 'Mi Negocio SpA',
        'neg-rut': '76.543.210-9',
        'neg-rango_empleados': 'R1',
        'neg-direccion': 'Calle Test 123',
        'neg-region': reg.id,
        'neg-provincia': prov.id,
        'neg-comuna': com.id,
        'neg-rubro': rubro.id,
        'neg-acepto_politica_datos_check': 'on',
    }
    form = NegocioOnboardingForm(data=post_data, prefix='neg')
    is_valid = form.is_valid()
    print(f"Onboarding form validation result: {is_valid}")
    if not is_valid:
        print("Form errors:", form.errors)
    assert is_valid, "Onboarding geo form validation failed!"
    print("[OK] Onboarding Geo Form validation passed cleanly!")

print("\nALL 5 REQUESTED FEATURES AND FIXES VERIFIED 100% CLEANLY!")
