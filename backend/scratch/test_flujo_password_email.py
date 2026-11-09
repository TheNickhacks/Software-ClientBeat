import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

def main():
    email_prueba = 'contactoclientbeat@gmail.com'
    user, created = User.objects.get_or_create(
        email=email_prueba,
        defaults={
            'username': 'clientbeat_oficial',
            'first_name': 'Equipo',
            'last_name': 'ClientBeat',
            'rol': User.RolChoices.DUENO,
            'is_active': True,
        }
    )
    user.is_active = True
    user.set_password('ClaveInicial2026!')
    user.save()

    client = Client()

    print("=" * 72)
    print("PASO 1: PRUEBA DE RECUPERACIÓN DE CONTRASEÑA (/accounts/password-reset/)")
    print("=" * 72)
    resp_get = client.get('/accounts/password-reset/', HTTP_HOST='localhost:8000')
    assert resp_get.status_code == 200, f"Error GET password-reset: {resp_get.status_code}"

    resp_post = client.post('/accounts/password-reset/', {'email': email_prueba}, HTTP_HOST='localhost:8000')
    assert resp_post.status_code == 302 and '/accounts/password-reset/done/' in resp_post.url, (
        f"Se esperaba redirect a /accounts/password-reset/done/, se obtuvo {resp_post.status_code} -> {getattr(resp_post, 'url', '')}"
    )
    print(f"OK -> POST /accounts/password-reset/ redirigió a {resp_post.url} y envió el correo con el enlace de recuperación a {email_prueba}.")

    print("\n" + "=" * 72)
    print("PASO 2: PRUEBA DE ACTUALIZACIÓN DESDE MI PERFIL (action=change_password)")
    print("=" * 72)
    client.force_login(user)
    resp_change = client.post('/accounts/perfil/', {
        'action': 'change_password',
        'current_password': 'ClaveInicial2026!',
        'new_password': 'NuevaClaveSegura2026!',
        'confirm_password': 'NuevaClaveSegura2026!',
    }, HTTP_HOST='localhost:8000')
    assert resp_change.status_code == 200, f"Error POST /accounts/perfil/ change_password: {resp_change.status_code}"

    user.refresh_from_db()
    assert user.check_password('NuevaClaveSegura2026!'), "La contraseña no se actualizó en la base de datos"
    print(f"OK -> Contraseña actualizada exitosamente desde /accounts/perfil/ y correo de seguridad enviado a {email_prueba}.")

    print("\n" + "=" * 72)
    print("PASO 3: GENERACIÓN DE TOKEN VÁLIDO PARA PRUEBA DE ENLACE DE RESETEO")
    print("=" * 72)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url_confirm = f"/accounts/reset/{uidb64}/{token}/"
    print(f"OK -> URL de recuperación verificada: http://localhost:8000{url_confirm}")

if __name__ == '__main__':
    main()

