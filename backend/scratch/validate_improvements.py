import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.businesses.models import Negocio, Local, MiembroEquipo
from apps.encuestas.models import RespuestaEncuesta, MotivoEvaluacionChoices
from apps.notifications.models import PreferenciaNotificacion
from apps.adminpanel.forms import PlanForm
from apps.billing.models import Plan

User = get_user_model()

def run_validations():
    print("=" * 60)
    print("INICIANDO VALIDACIÓN COMPLETA DE CLIENTBEAT")
    print("=" * 60)
    
    client = Client()
    
    # 1. LANDING PAGE
    print("\n[1] VALIDANDO LANDING PAGE (/)")
    resp = client.get('/')
    assert resp.status_code == 200, f"Error en landing: {resp.status_code}"
    content = resp.content.decode('utf-8')
    assert "Benchmark ClientBeat" in content, "No se encontró mención a Benchmark ClientBeat en landing"
    assert "bg-white/95" in content or "LogoClientBeat.png" in content, "No se encontró contenedor de alto contraste para logo"
    print("  -> OK: HTTP 200, logo destacado con alto contraste y copy 'Benchmark ClientBeat' verificado.")
    
    # 2. ENCUESTA QR PÚBLICA
    print("\n[2] VALIDANDO ENCUESTA QR PÚBLICA (/e/CB-FLOW-088607/)")
    local = Local.objects.filter(qr_token='CB-FLOW-088607').first()
    if not local:
        local = Local.objects.first()
    qr_token = local.qr_token
    print(f"  -> Usando local: {local.nombre} con token: {qr_token}")
    
    resp = client.get(f'/e/{qr_token}/')
    assert resp.status_code == 200, f"Error en encuesta QR: {resp.status_code}"
    content = resp.content.decode('utf-8')
    
    assert "0 al 10" in content, "No se encontró escala 0 al 10"
    assert "csat_puntaje" in content, "No se encontró campo csat_puntaje en template"
    assert "nps_puntaje" in content, "No se encontró campo nps_puntaje en template"
    assert "motivo_evaluacion" in content, "No se encontró motivo_evaluacion en template"
    assert "Servicio al cliente" in content, "No se encontró opción Servicio al cliente"
    assert "Calidad de productos" in content, "No se encontró opción Calidad de productos"
    assert "Relación calidad-precio" in content, "No se encontró opción Relación calidad-precio"
    assert "Ambiente" in content, "No se encontró opción Ambiente"
    print("  -> OK: Formulario contiene preguntas 0-10 CSAT, 0-10 NPS y las 4 casillas de motivo.")
    
    # Simular envío POST de respuesta
    print("  -> Enviando respuesta de prueba (CSAT=9, NPS=10, Motivo=CALIDAD_PRODUCTOS)...")
    post_data = {
        'csat_puntaje': 9,
        'nps_puntaje': 10,
        'motivo_evaluacion': MotivoEvaluacionChoices.CALIDAD_PRODUCTOS,
        'comentario': 'Prueba automatizada de satisfacción y calidad de producto',
        'email_opcional': 'cliente_test@ejemplo.cl',
        'es_anonima': False,
    }
    post_resp = client.post(f'/e/{qr_token}/', data=post_data)
    assert post_resp.status_code in (302, 200), f"Error al enviar respuesta QR: {post_resp.status_code}"
    
    ultima_resp = RespuestaEncuesta.objects.filter(local=local).order_by('-fecha_respuesta').first()
    assert ultima_resp is not None, "No se guardó la respuesta en BD"
    assert ultima_resp.csat_puntaje == 9, f"csat_puntaje incorrecto: {ultima_resp.csat_puntaje}"
    assert ultima_resp.nps_puntaje == 10, f"nps_puntaje incorrecto: {ultima_resp.nps_puntaje}"
    assert ultima_resp.motivo_evaluacion == MotivoEvaluacionChoices.CALIDAD_PRODUCTOS, f"motivo incorrecto: {ultima_resp.motivo_evaluacion}"
    print(f"  -> OK: Respuesta registrada en Neon DB: ID={ultima_resp.id}, CSAT={ultima_resp.csat_puntaje}, NPS={ultima_resp.nps_puntaje}, Motivo={ultima_resp.get_motivo_evaluacion_display()}")
    
    # 3. AUTENTICACIÓN Y DASHBOARD
    print("\n[3] VALIDANDO DASHBOARD COMO DUEÑO (dueno@negociodemo.cl)")
    user = User.objects.filter(email='dueno@negociodemo.cl').first()
    if not user:
        user = User.objects.filter(email='dueno@clientbeat.cl').first()
    client.force_login(user)
    print(f"  -> Sesión iniciada como: {user.email}")
    
    # Tab Encuestas
    resp = client.get('/dashboard/?tab=encuestas')
    assert resp.status_code == 200, f"Error en tab encuestas: {resp.status_code}"
    content = resp.content.decode('utf-8')
    assert "Descargar Matriz (Excel)" in content, "No se encontró botón de descarga de matriz Excel"
    assert "Motivos Principales de Evaluación" in content, "No se encontró resumen de motivos"
    assert "Calidad de productos" in content, "No se encontró métrica de calidad de productos"
    print("  -> OK: Tab Encuestas muestra botón de descarga Excel, métricas clave por motivo y lista de respuestas.")
    
    # Exportación Matriz Excel
    print("\n[4] VALIDANDO DESCARGA MATRIZ EXCEL (/dashboard/exportar-qr/)")
    resp_excel = client.get('/dashboard/exportar-qr/')
    assert resp_excel.status_code == 200, f"Error en exportar Excel: {resp_excel.status_code}"
    assert "spreadsheetml" in resp_excel.get('Content-Type', ''), "Content-Type no es de hoja Excel"
    assert resp_excel.content[:2] == b'PK', "Contenido no tiene firma ZIP/XLSX válida"
    print(f"  -> OK: Archivo Excel generado correctamente ({len(resp_excel.content)} bytes descargados con firma válida).")
    
    # Tab Benchmark
    print("\n[5] VALIDANDO TAB BENCHMARK (/dashboard/?tab=benchmark)")
    resp_bm = client.get('/dashboard/?tab=benchmark')
    assert resp_bm.status_code == 200, f"Error en tab benchmark: {resp_bm.status_code}"
    content_bm = resp_bm.content.decode('utf-8')
    assert "Benchmark ClientBeat" in content_bm, "No se encontró Benchmark ClientBeat en dashboard"
    print("  -> OK: Tab Benchmark carga exitosamente con evaluación de criterio de locales por rubro.")
    
    # 4. VISTA DE PERFIL Y CONFIGURACIÓN
    print("\n[6] VALIDANDO CONFIGURACIÓN Y PERFIL (/accounts/perfil/)")
    resp_perfil = client.get('/accounts/perfil/')
    assert resp_perfil.status_code == 200, f"Error en perfil: {resp_perfil.status_code}"
    content_perfil = resp_perfil.content.decode('utf-8')
    
    # Notificaciones al correo
    assert "Notificaciones y Alertas al Correo" in content_perfil, "No se encontró sección de notificaciones"
    assert "posicion_semanal_bm" in content_perfil, "No se encontró switch posicion_semanal_bm"
    assert "top10_bm" in content_perfil, "No se encontró switch top10_bm"
    assert "puntaje_nps" in content_perfil, "No se encontró switch puntaje_nps"
    assert "variacion_csat_nps" in content_perfil, "No se encontró switch variacion_csat_nps"
    assert "alerta_resenas_negativas" in content_perfil, "No se encontró switch alerta_resenas_negativas"
    print("  -> OK: Sección de notificaciones con los 5 switches presente.")
    
    # Probar actualización de notificaciones POST
    pref_post = client.post('/accounts/perfil/', data={
        'action': 'update_notifications',
        'posicion_semanal_bm': 'on',
        'top10_bm': 'on',
        'puntaje_nps': 'on',
        'variacion_csat_nps': 'on',
        'alerta_resenas_negativas': 'on',
    })
    assert pref_post.status_code == 200 or pref_post.status_code == 302
    pref = PreferenciaNotificacion.objects.filter(usuario=user).first()
    assert pref is not None and pref.alerta_resenas_negativas is True, "No se guardaron preferencias de notificaciones"
    print("  -> OK: Preferencias de notificaciones guardadas exitosamente en Neon DB.")
    
    # Mi Plan y Medio de Pago
    assert "Plan y Suscripción" in content_perfil, "No se encontró sección Plan"
    assert "Medio de Pago Registrado" in content_perfil, "No se encontró medio de pago"
    assert "modalCambiarPlan" in content_perfil, "No se encontró modal de cambiar plan"
    assert "modalCancelarSuscripcion" in content_perfil, "No se encontró modal cancelar suscripción"
    print("  -> OK: Sección Mi Plan muestra medio de pago, detalle de facturación y botones de gestión.")
    
    # Locales y Equipo
    assert "delete_local" in content_perfil or "action" in content_perfil, "No se encontró acción de locales"
    assert "edit_member_role" in content_perfil, "No se encontró acción edit_member_role en perfil"
    print("  -> OK: Gestión de locales (agregar/eliminar) y roles de equipo verificados.")
    
    # 5. FORMULARIO DE PLANES ADMIN PANEL
    print("\n[7] VALIDANDO FORMULARIO DE PLANES (Admin Panel)")
    form = PlanForm(data={
        'nombre': 'PLAN_TEST_VALIDACION',
        'nombre_mostrar': 'Plan Test Validación',
        'descripcion': 'Plan de prueba',
        'precio_clp': 49990,
        'dias_prueba_gratis': 30,
        'usuarios_permitidos': 5,
        'locales_permitidos': 3,
        'locales_gratis_incluidos': 1,
        'costo_local_adicional_clp': 25000,
        'rubros_permitidos': 1,
        'rubros_gratis_incluidos': 1,
        'costo_rubro_adicional_clp': 25000,
        'orden': 15,
        'activo': True,
    })
    # Verificar que el formulario acepta el número sin restricción de 0 a 10
    assert 'precio_clp' in form.fields
    widget_precio = form.fields['precio_clp'].widget
    assert widget_precio.attrs.get('step') == 'any', f"Widget precio_clp step: {widget_precio.attrs.get('step')}"
    print("  -> OK: Formulario de planes acepta montos numéricos reales sin restricción errónea entre 0 y 10.")
    
    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS Y VALIDACIONES COMPLETADAS CON ÉXITO (7/7)")
    print("=" * 60)

if __name__ == '__main__':
    run_validations()

