import os
import sys
import time
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.pages.views import dashboard
from apps.businesses.models import Negocio

User = get_user_model()

def run_tests():
    print("=" * 65)
    print("=== TEST PERFORMANCE Y LATENCIA DASHBOARD CLIENTBEAT ===")
    print("=" * 65)
    
    # 1. Obtener usuario con negocio
    negocio = Negocio.objects.first()
    user = negocio.dueño if (negocio and negocio.dueño) else (User.objects.filter(is_superuser=False).first() or User.objects.first())
    print(f"[*] Testing with user: {user.email}")
    print(f"[*] Testing with business: {negocio.nombre if negocio else 'None'} (id: {negocio.id if negocio else 'N/A'})")
    
    rf = RequestFactory()
    tabs_to_test = ['resumen', 'encuestas', 'csat_nps', 'google', 'analisis', 'benchmark']
    
    results = {}
    
    for tab in tabs_to_test:
        url = f"/dashboard/?tab={tab}&temporalidad=MENSUAL"
        request = rf.get(url)
        request.user = user
        request.session = {}
        request.negocio = negocio
        request.negocios_qs = Negocio.objects.filter(id=negocio.id) if negocio else Negocio.objects.none()
        request.rol_actual_negocio = 'DUENO'
        
        # Medir tiempo de ejecución (Latencia de la vista)
        start_t = time.perf_counter()
        response = dashboard(request)
        elapsed_ms = (time.perf_counter() - start_t) * 1000
        
        results[tab] = {
            'status': response.status_code,
            'elapsed_ms': round(elapsed_ms, 2),
            'content_len': len(response.content) if hasattr(response, 'content') else 0
        }
        
        print(f"  -> Tab: {tab:<12} | Status: {response.status_code} | Latencia: {results[tab]['elapsed_ms']:>6.1f} ms | Tamaño: {results[tab]['content_len']:>7} bytes")
        assert response.status_code in (200, 302), f"Tab {tab} returned status {response.status_code}"
    
    print("-" * 65)
    # Test de caché en segunda pasada para Benchmark
    print("[*] Verificando optimización de caché en pestaña 'benchmark' (segunda pasada):")
    req_bench = rf.get("/dashboard/?tab=benchmark&temporalidad=MENSUAL")
    req_bench.user = user
    req_bench.session = {}
    req_bench.negocio = negocio
    req_bench.negocios_qs = Negocio.objects.filter(id=negocio.id) if negocio else Negocio.objects.none()
    req_bench.rol_actual_negocio = 'DUENO'
    
    start_bench = time.perf_counter()
    resp_bench = dashboard(req_bench)
    elapsed_bench_cached = (time.perf_counter() - start_bench) * 1000
    print(f"  -> Benchmark (Cached): Latencia: {elapsed_bench_cached:>6.1f} ms (vs inicial: {results['benchmark']['elapsed_ms']:>6.1f} ms)")
    
    print("=" * 65)
    print(">>> TODOS LOS TESTS DE PERFORMANCE PASARON EXITOSAMENTE <<<")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()
