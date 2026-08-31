import os
import sys

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.businesses.models import Negocio
from apps.billing.models import Suscripcion

User = get_user_model()
admin_user = User.objects.filter(email='admin@clientbeat.cl').first()

client = Client()
client.force_login(admin_user)

negocio_demo = Negocio.objects.first()
sus_demo = Suscripcion.objects.first()

urls_to_test = [
    '/admin-panel/',
    '/admin-panel/perfil/',
    '/admin-panel/preview-cliente/',
    '/admin-panel/reporteria/clientes/',
    '/admin-panel/reporteria/benchmark-rubro/',
    '/admin-panel/reporteria/tendencias-resenas/',
    '/admin-panel/reporteria/planes/',
    '/admin-panel/data-google/rubros/',
    '/admin-panel/metricas/criterios-benchmark/',
    '/admin-panel/metricas/csat-nps/',
    '/admin-panel/metricas/resenas-google/',
    '/admin-panel/planes/editar/',
    '/admin-panel/recursos/reconocimiento/',
    '/admin-panel/notificaciones/',
    '/admin-panel/auditoria/',
    '/admin-panel/usuarios/',
]

if negocio_demo:
    urls_to_test.append(f'/admin-panel/clientes/{negocio_demo.id}/')
    urls_to_test.append(f'/admin-panel/suscripciones/nueva/?negocio_id={negocio_demo.id}')

if sus_demo:
    urls_to_test.append(f'/admin-panel/suscripciones/{sus_demo.id}/')

print("Testing all Admin Panel main and detail views...")
failed = False
for url in urls_to_test:
    try:
        response = client.get(url, follow=True)
        if response.status_code == 200:
            print(f"[OK 200] {url}")
        else:
            print(f"[FAIL {response.status_code}] {url}")
            failed = True
    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
        failed = True

if not failed:
    print("\nALL ADMIN PANEL ENDPOINTS AND DETAIL VIEWS PASSED CLEANLY (200 OK)!")
else:
    print("\nSOME ENDPOINTS FAILED!")
