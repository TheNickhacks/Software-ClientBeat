from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

from apps.accounts.onboarding_service import onboarding_pendiente, onboarding_siguiente_paso


TERMINOS_Y_CONDICIONES = """
1. OBJETO Y ACEPTACIÓN
Client Beat es una plataforma de software como servicio (SaaS) que permite a dueños de negocios monitorear, en un panel centralizado, su reputación digital, compararla con la de sus competidores directos y capturar la opinión de sus propios clientes en el punto de venta, sin requerir conocimientos técnicos.
Al registrarse, acceder o utilizar el Servicio, el Cliente acepta íntegra y vinculantemente estos Términos y Condiciones. Si el Cliente no está de acuerdo con ellos, deberá abstenerse de registrarse o de utilizar la plataforma.

2. DEFINICIONES
Cliente: persona natural o jurídica que se registra y contrata el Servicio para su negocio.
Servicio o Plataforma: Client Beat, incluyendo su sitio web, panel de administración, motor de reputación y benchmarking, módulo de encuestas por código QR, motor de análisis de sentimiento y pasarela de pagos integrada.
Tenant: la instancia lógica y aislada de datos correspondiente a cada Cliente dentro de la arquitectura multi-tenant de la Plataforma.

3. DESCRIPCIÓN DEL SERVICIO (PLAN MVP)
El plan inicial contratado comprende:
• Reputación y benchmarking de competencia mediante Google Places API.
• Captura de voz directa mediante encuestas QR (NPS y CSAT).
• Motor de análisis de sentimiento léxico con modismos chilenos.
• Ciclo completo de suscripción y pago a través de Flow.

4. REGISTRO Y CUENTA
El Cliente debe ser mayor de 18 años y declarar esta condición al registrarse.
Client Beat no almacena contraseñas en texto plano ni tiene acceso a la contraseña del Cliente.
El Cliente es responsable de la confidencialidad de sus credenciales.

5. CONDICIONES ECONÓMICAS Y FACTURACIÓN
Los precios se expresan en UF o CLP, netos de IVA, conforme a la práctica comercial chilena.
La suscripción se renueva automáticamente al vencimiento de cada ciclo de facturación salvo cancelación oportuna.
En caso de mora, el acceso a la Plataforma podrá suspenderse.

6. PASARELA DE PAGOS FLOW
El cobro se procesa exclusivamente en los servidores de Flow. Client Beat no almacena datos de tarjetas.
Las notificaciones de pago se validan mediante firma digital antes de activar suscripciones.

7. PROPIEDAD INTELECTUAL
Client Beat conserva todos los derechos sobre su software, algoritmos y diseño. El Cliente conserva la titularidad de sus propios datos.

8. DISPONIBILIDAD Y RESPONSABILIDAD
El Servicio se presta "tal como está". La responsabilidad de Client Beat se limita al monto pagado en los últimos 12 meses.

9. PROTECCIÓN DE DATOS PERSONALES
Client Beat SpA (RUT 77.607.311-3) actúa como responsable del tratamiento. Los titulares pueden ejercer sus derechos ARCOPB al correo contacto@avaapp.cl.

10. LEY APLICABLE Y JURISDICCIÓN
Estos Términos se rigen por las leyes de la República de Chile y se someten a la jurisdicción de los tribunales ordinarios justicia.

Versión inicial — Agosto 2026.
"""

POLITICA_PRIVACIDAD = """
1. RESPONSABLE DEL TRATAMIENTO
Nombre: Client Beat SpA
RUT: 77.607.311-3
Domicilio: Asturias 790 E, Rancagua
Correo contacto: contacto@avaapp.cl

2. CATEGORÍAS DE DATOS
• Datos del Cliente: nombre o razón social, RUT, rubro, datos de contacto, credenciales, facturación.
• Datos de clientes finales: respuestas de satisfacción, comentarios, calificaciones, reseñas públicas de Google.
• Datos de navegación: registros técnicos de acceso, direcciones IP, logs de actividad.

3. FINALIDAD DEL TRATAMIENTO
• Gestión del registro y la relación contractual.
• Prestación del Servicio: reputación, benchmarking, encuestas, análisis de sentimiento.
• Cumplimiento de obligaciones legales y tributarias.

4. BASE DE LICITUD
El tratamiento se funda en la ejecución del contrato (servicio contratado), el consentimiento del titular (encuestas QR) y el interés legítimo del responsable (benchmarking anonimizado).

5. DERECHOS DEL TITULAR (ARCOPB)
Todo titular puede ejercer gratuitamente sus derechos de Acceso, Rectificación, Cancelación/Supresión, Oposición, Portabilidad y Bloqueo escribiendo a contacto@avaapp.cl. Plazo de respuesta: 30 días, prorrogables por 30 más.

6. CONSERVACIÓN
• Datos tributarios: 6 años.
• Logs de navegación: 12 meses.
• Datos de encuestas: hasta que el titular solicite su supresión.

7. TRANSFERENCIAS INTERNACIONALES
Neon (PostgreSQL), Google Places API y proveedores de correo pueden implicar transferencias internacionales. Se adoptan las garantías legales correspondientes.

8. SEGURIDAD
Aislamiento lógico multi-tenant, cifrado SSL/TLS, hashing de credenciales, respaldos periódicos y procedimiento de notificación de brechas.

9. NOTIFICACIÓN DE BRECHAS
En caso de vulnerabilidad relevante, se notificará a la Agencia de Protección de Datos y a los titulares afectados sin dilación indebida.
"""

POLITICA_COOKIES = """
¿Qué son las cookies?
Las cookies son pequeños archivos de texto que se almacenan en tu navegador al visitar una página web. Nos permiten recordar tus preferencias y mejorar la experiencia.

Cookies que utilizamos en Client Beat:
1. Cookies esenciales: necesarias para el funcionamiento del sitio (sesión de usuario, carrito, seguridad CSRF). No pueden desactivarse.
2. Cookies analíticas (opcionales): para medir el tráfico y mejorar el servicio.

Cómo gestionar las cookies
Puedes eliminar o bloquear las cookies desde la configuración de tu navegador. Ten en cuenta que algunas funcionalidades del sitio podrían dejar de funcionar correctamente.

Al continuar navegando por www.clientbeat.cl, aceptas nuestra política de cookies.
"""


_CONTENIDOS_LEGALES = {
    'terminos': {
        'titulo': 'Términos y Condiciones de Servicio',
        'fecha': '04 de Agosto del 2026',
        'contenido': TERMINOS_Y_CONDICIONES.strip(),
    },
    'privacidad': {
        'titulo': 'Política de Privacidad y Protección de Datos',
        'fecha': '04 de Agosto del 2026',
        'contenido': POLITICA_PRIVACIDAD.strip(),
    },
    'cookies': {
        'titulo': 'Política de Cookies',
        'fecha': '04 de Agosto del 2026',
        'contenido': POLITICA_COOKIES.strip(),
    },
}


def landing(request):
    return render(request, 'landing.html')


@login_required(login_url='/accounts/login/')
def dashboard(request):
    if onboarding_pendiente(request.user):
        paso, _ = onboarding_siguiente_paso(request.user)
        return redirect(f'/accounts/onboarding/?paso={paso}')
    ctx = {
        'welcome': request.GET.get('welcome') == '1',
        'negocio': getattr(request, 'negocio', None),
        'negocios_qs': getattr(request, 'negocios_qs', None),
        'rol_actual': getattr(request, 'rol_actual_negocio', None),
    }
    negocio = ctx['negocio']
    if negocio is not None:
        from apps.billing.models import Suscripcion, EstadoSuscripcionChoices
        suscripcion = (
            Suscripcion.objects
            .filter(negocio=negocio, estado=EstadoSuscripcionChoices.ACTIVA)
            .select_related('plan')
            .order_by('-fecha_inicio')
            .first()
        )
        ctx['suscripcion_activa'] = suscripcion
        ctx['plan_activo'] = suscripcion.plan if suscripcion else None
    return render(request, 'dashboard_placeholder.html', ctx)


def legal(request, slug):
    data = _CONTENIDOS_LEGALES.get(slug)
    if not data:
        data = _CONTENIDOS_LEGALES['terminos']
    ctx = {
        'titulo': data['titulo'],
        'fecha_actualizacion': data['fecha'],
        'contenido': data['contenido'],
    }
    return render(request, 'legal.html', ctx)
