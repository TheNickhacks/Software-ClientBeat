import os
import sys
import django

sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('backend/apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail


def test_envio_real_gmail():
    print("=" * 70)
    print("PROBANDO ENVIO REAL DE CORREO SMTP DESDE contactoclientbeat@gmail.com")
    print("=" * 70)
    print(f"EMAIL_BACKEND   : {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST      : {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (TLS={settings.EMAIL_USE_TLS})")
    print(f"EMAIL_HOST_USER : {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM    : {settings.DEFAULT_FROM_EMAIL}")

    enviados = send_mail(
        subject="✅ Prueba de Conexión SMTP Oficial — ClientBeat SpA",
        message=(
            "¡Hola!\n\n"
            "Este es un correo real enviado automáticamente desde la plataforma ClientBeat "
            "utilizando el servidor SMTP de Gmail (contactoclientbeat@gmail.com).\n\n"
            "• Motor de Suscripciones Flow Chile: Operativo\n"
            "• Alertas Dunning (3 días de gracia): Operativas\n"
            "• Invitaciones de Colaboradores y Alertas NPS/CSAT: Operativas\n\n"
            "Client Beat SpA · Asturias 790, Rancagua · www.clientbeat.cl"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print(f"\n[OK] Correos enviados exitosamente: {enviados}")
    assert enviados == 1


if __name__ == '__main__':
    test_envio_real_gmail()

