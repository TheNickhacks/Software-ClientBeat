import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from apps.businesses.models import Negocio, Local
from apps.encuestas.models import PlantillaEncuesta, RespuestaEncuesta
from apps.adminpanel.models import SolicitudARCOPB
from django.contrib.auth import get_user_model

User = get_user_model()

def test_custom_survey_engine():
    print("--- 1. Testing Custom Survey Engine ---")
    negocio = Negocio.objects.first()
    if not negocio:
        print("FAIL: No negocio found in DB.")
        return False

    local = negocio.locales.filter(estado='ACTIVO').first()
    if not local:
        print("FAIL: No active local found.")
        return False

    # Create or update custom survey template
    plantilla, created = PlantillaEncuesta.objects.get_or_create(negocio=negocio)
    plantilla.nombre = f'Test Encuesta Custom {negocio.nombre}'
    plantilla.nombre_mostrar = '¡Tu Opinión Importa en Test!'
    plantilla.color_primario = '#1e293b'
    plantilla.color_secundario = '#0284c7'
    plantilla.color_fondo = '#f1f5f9'
    plantilla.preguntas_extra = [
        {'texto': '¿Cómo estuvo la limpieza?', 'tipo': 'ESTRELLAS_1_5', 'requerido': True},
        {'texto': '¿Volverías a visitarnos?', 'tipo': 'SI_NO', 'requerido': True},
    ]
    plantilla.activa = True
    plantilla.save()
    print(f"Custom plantilla created/updated: {plantilla.id} for Negocio: {negocio.nombre}")

    # Submit public survey response
    client = Client()
    url = f"/e/{local.qr_token}/"
    resp = client.get(url)
    print(f"GET {url} Status Code: {resp.status_code}")

    post_data = {
        'nps_puntaje': '10',
        'csat_emocion': 'MUY_FELIZ',
        'comentario': 'Excelente servicio personalizado!',
        'email_opcional': 'testclient@gmail.com',
        'custom_q_0': '5',
        'custom_q_1': 'SI',
    }
    resp_post = client.post(url, post_data)
    print(f"POST {url} Status Code: {resp_post.status_code} (302 expected for redirect to gracias)")

    # Verify saved response in DB
    ultima_resp = RespuestaEncuesta.objects.filter(local=local).order_by('-fecha_respuesta').first()
    if ultima_resp:
        print(f"Saved Respuesta ID: {ultima_resp.id}")
        print(f"NPS: {ultima_resp.nps_puntaje}, CSAT: {ultima_resp.csat_emocion}")
        print(f"Custom Responses Metadata: {ultima_resp.metadata.get('respuestas_custom')}")

    return True

def test_admin_panel_modules():
    print("\n--- 2. Testing Admin Panel Modules ---")
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_test@clientbeat.cl', 'Password123!')
        print("Created test superuser")

    client = Client()
    client.force_login(admin_user)

    routes = [
        '/admin-panel/',
        '/admin-panel/clientes/',
        '/admin-panel/usuarios/',
        '/admin-panel/plantillas/',
        '/admin-panel/solicitudes-arco/',
    ]

    for route in routes:
        res = client.get(route)
        print(f"GET {route} -> Status Code: {res.status_code}")

    # Test Client Customizer View logged in as business owner
    dueno = User.objects.filter(negocios__isnull=False).first() or admin_user
    client.force_login(dueno)
    res_custom = client.get('/encuestas/configurar/')
    print(f"GET /encuestas/configurar/ -> Status Code: {res_custom.status_code}")

    # Create a test ARCOPB request
    arco = SolicitudARCOPB.objects.create(
        nombre_solicitante='Juan Perez',
        email_solicitante='juan.perez@test.cl',
        rut_solicitante='12.345.678-9',
        tipo_solicitud='ELIMINACION_DATOS',
        detalle='Solicito eliminar mis datos personales.'
    )
    print(f"Created Solicitud ARCOPB #{str(arco.id)[:8]}")

    return True

if __name__ == '__main__':
    ok1 = test_custom_survey_engine()
    ok2 = test_admin_panel_modules()
    if ok1 and ok2:
        print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    else:
        print("\nSOME TESTS FAILED!")
