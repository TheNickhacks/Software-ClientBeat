import os
import sys
import django

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(is_superuser=True).first()

c = Client()
c.force_login(user)

urls = [
    '/admin-panel/reporteria/clientes/',
    '/admin-panel/reporteria/clientes/export/',
    '/admin-panel/reporteria/benchmark-google/',
    '/admin-panel/reporteria/benchmark-google/export/',
    '/admin-panel/reporteria/benchmark-clientbeat/',
    '/admin-panel/reporteria/benchmark-clientbeat/export/',
    '/admin-panel/reporteria/benchmark-nps-csat/',
    '/admin-panel/reporteria/benchmark-nps-csat/export/',
    '/admin-panel/reporteria/tendencias-resenas/',
    '/admin-panel/reporteria/tendencias-resenas/export/',
    '/admin-panel/reporteria/planes/',
    '/admin-panel/reporteria/planes/export/',
]

print("=== VERIFICACIÓN DE ENDPOINTS DE REPORTERÍA Y EXPORTACIÓN EXCEL ===", flush=True)
for url in urls:
    resp = c.get(url)
    ct = resp.headers.get('Content-Type')
    print(f"URL: {url:55} -> STATUS: {resp.status_code} | TYPE: {ct}", flush=True)
