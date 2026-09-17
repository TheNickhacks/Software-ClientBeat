import os
import sys
import time
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from apps.businesses.models import Local, Negocio
from django.contrib.auth import get_user_model

User = get_user_model()

def benchmark_pages():
    client = Client()
    user = User.objects.filter(negocios__isnull=False).first() or User.objects.filter(is_superuser=True).first()
    client.force_login(user)

    local = Local.objects.filter(estado='ACTIVO').first()
    qr_token = local.qr_token if local else 'test'

    urls = [
        ('/', 'Landing Page'),
        ('/dashboard/', 'Client Dashboard (Resumen Tab)'),
        ('/dashboard/?tab=analisis', 'Client Dashboard (Análisis Tab)'),
        ('/dashboard/?tab=google', 'Client Dashboard (Google Tab)'),
        ('/dashboard/?tab=benchmark', 'Client Dashboard (Benchmark Tab)'),
        (f'/e/{qr_token}/', 'Encuesta Pública QR'),
        ('/encuestas/configurar/', 'Motor Encuestas Customizer'),
        ('/admin-panel/', 'Admin Panel Dashboard'),
        ('/admin-panel/clientes/', 'Admin Panel Clientes List'),
        ('/admin-panel/usuarios/', 'Admin Panel Usuarios List'),
        ('/admin-panel/plantillas/', 'Admin Panel Plantillas List'),
        ('/admin-panel/solicitudes-arco/', 'Admin Panel Solicitudes ARCOPB List'),
    ]

    print("=" * 65)
    print(f"{'ROUTE':<40} | {'STATUS':<7} | {'TIME (ms)':<10}")
    print("=" * 65)

    for path, label in urls:
        start = time.perf_counter()
        resp = client.get(path)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"{path:<40} | {resp.status_code:<7} | {elapsed_ms:>7.1f} ms")

    print("=" * 65)

if __name__ == '__main__':
    benchmark_pages()
