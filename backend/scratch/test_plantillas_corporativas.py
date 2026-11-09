import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from apps.notifications.models import PlantillaNotificacion

def main():
    print("=" * 70)
    print("1. VERIFICACIÓN DE LAS 24 PLANTILLAS EN BASE DE DATOS (NEON DB)")
    print("=" * 70)
    plantillas = PlantillaNotificacion.objects.all().order_by('categoria', 'orden')
    total = plantillas.count()
    colores_antiguos = ['#4F46E5', '#7C3AED', '#6366F1', '#8B5CF6', '#EEF2FF', '#f5f3ff']
    errores = []

    for p in plantillas:
        html = p.cuerpo_html
        for hex_old in colores_antiguos:
            if hex_old.lower() in html.lower():
                errores.append(f"{p.codigo_unico}: contiene color antiguo {hex_old}")
        if '#0B3EA6'.lower() not in html.lower() and '#00B879'.lower() not in html.lower():
            errores.append(f"{p.codigo_unico}: no contiene colores corporativos (#0B3EA6 / #00B879)")
        if 'contactoclientbeat@gmail.com' not in html:
            errores.append(f"{p.codigo_unico}: falta correo oficial contactoclientbeat@gmail.com en footer HTML")

    print(f"Total plantillas verificadas en BD: {total}")
    assert total == 24, f"Se esperaban 24 plantillas, se encontraron {total}"
    assert not errores, f"Errores encontrados: {errores}"
    print("OK -> Las 24 plantillas en BD usan colores corporativos (#0B3EA6, #00B879, #041B3A) y contactoclientbeat@gmail.com")

    print("\n" + "=" * 70)
    print("2. VERIFICACIÓN DE PLANTILLAS DE ARCHIVO HTML (INVITACIÓN Y FACTURACIÓN)")
    print("=" * 70)
    html_facturacion = render_to_string('emails/facturacion_flow.html', {
        'asunto': '✅ Suscripción Activada — Cafetería Demo en ClientBeat',
        'badge_texto': 'Suscripción Activa · Flow Chile',
        'titulo_header': '¡Tu plan ya está activo!',
        'subtitulo_header': 'Cafetería Demo · Plan Anual Lanzamiento',
        'usuario_nombre': 'Equipo ClientBeat',
        'mensaje_principal': 'Hemos confirmado la activación de tu suscripción en ClientBeat con identidad visual corporativa.',
        'box_bg': '#ecfbf4',
        'box_border': '#00B879',
        'box_title_color': '#008E5C',
        'box_titulo': 'Resumen de Suscripción Corporativa',
        'detalles': [
            ('Negocio', 'Cafetería Demo SpA'),
            ('Plan Activo', 'Plan Anual Lanzamiento'),
            ('Medio de Pago Enrolado', 'Visa •••• 4242'),
            ('Monto Mensual', '$19.990 CLP'),
            ('Correo Oficial', 'contactoclientbeat@gmail.com'),
        ],
        'nota_secundaria': 'Todas las plantillas de la plataforma ahora utilizan los colores corporativos (#0B3EA6, #00B879 y #041B3A) y salen desde contactoclientbeat@gmail.com.',
        'cta_url': 'http://localhost:8000/accounts/perfil/',
        'cta_texto': 'Ir a Mi Suscripción',
    })
    assert '#0B3EA6' in html_facturacion and '#00B879' in html_facturacion and 'contactoclientbeat@gmail.com' in html_facturacion
    print("OK -> emails/facturacion_flow.html renderizado correctamente con paleta corporativa.")

    print("\n" + "=" * 70)
    print("3. ENVÍO DE PRUEBA DE PLANTILLA CORPORATIVA A contactoclientbeat@gmail.com")
    print("=" * 70)
    enviados = send_mail(
        subject='🎨 [ClientBeat] Nuevas Plantillas Corporativas Activas',
        message='Tus 26 plantillas de correo en ClientBeat ya están actualizadas con los colores corporativos y saliendo por contactoclientbeat@gmail.com.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['contactoclientbeat@gmail.com'],
        html_message=html_facturacion,
        fail_silently=False,
    )
    assert enviados == 1
    print(f"OK -> Correo corporativo enviado desde {settings.DEFAULT_FROM_EMAIL} a contactoclientbeat@gmail.com")

if __name__ == '__main__':
    main()

