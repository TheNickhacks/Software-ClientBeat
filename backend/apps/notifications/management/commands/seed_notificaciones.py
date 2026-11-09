from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.notifications.models import (
    PlantillaNotificacion,
    CategoriaNotificacionChoices,
)


PLANTILLAS = [
    # =============================================================
    # CATEGORÍA 1: ONBOARDING (4 plantillas)
    # =============================================================
    {
        "codigo_unico": "ONBOARD-001-BIENVENIDA-DUENO",
        "categoria": CategoriaNotificacionChoices.ONBOARDING,
        "nombre": "Bienvenida Dueño Negocio",
        "asunto_email": "🎉 ¡Bienvenido a ClientBeat, {{negocio}}! Tu panel ya está listo.",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Gracias por elegir ClientBeat para {{negocio}}.\n"
            "Tu plan {{plan}} ya está activo.\n"
            "Accede al dashboard: {{dashboard_url}}\n\n"
            "Cordialmente,\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;font-family:Arial,sans-serif;color:#1f2937;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:32px;text-align:center;color:#fff;border-radius:16px 16px 0 0;">
    <h1 style="margin:0;font-size:28px;">🎉 ¡Bienvenido a ClientBeat!</h1>
    <p style="opacity:0.95;margin-top:8px;">Hola {{usuario}}, gracias por elegirnos.</p>
  </div>
  <div style="background:#fff;padding:32px;border:1px solid #d9e7ff;border-top:none;">
    <p style="font-size:16px;line-height:1.6;">Tu negocio <strong>{{negocio}}</strong> ya está registrado con el plan <strong>{{plan}}</strong>.</p>
    <p style="font-size:16px;line-height:1.6;">Siguientes pasos sugeridos:</p>
    <ol style="font-size:16px;line-height:1.8;">
      <li>Configura tus <strong>locales y QR</strong></li>
      <li>Personaliza la <strong>identidad visual</strong></li>
      <li>Invita a tu <strong>equipo</strong></li>
    </ol>
    <div style="text-align:center;margin-top:28px;">
      <a href="{{dashboard_url}}" style="display:inline-block;background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:700;">
        Ir al Dashboard →
      </a>
    </div>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 16px 16px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "negocio", "plan", "dashboard_url"],
        "activo": True,
        "orden": 1,
    },
    {
        "codigo_unico": "ONBOARD-002-CONFIRMA-EMAIL",
        "categoria": CategoriaNotificacionChoices.ONBOARDING,
        "nombre": "Confirmación Email Usuario",
        "asunto_email": "📩 Confirma tu correo en ClientBeat",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Confirma tu dirección de email para activar tu cuenta:\n"
            "{{confirmacion_url}}\n\n"
            "Si no solicitaste esto, ignóralo.\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:560px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:24px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <h2 style="margin:0;">📩 Confirma tu correo</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:32px;">
    <p>Hola <strong>{{usuario}}</strong>,</p>
    <p>Por favor confirma tu email para completar el registro:</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{{confirmacion_url}}" style="background:#00B879;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:700;">
        ✅ Confirmar Email
      </a>
    </div>
    <p style="font-size:13px;color:#6b7280;">O copia y pega: {{confirmacion_url}}</p>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "confirmacion_url"],
        "activo": True,
        "orden": 2,
    },
    {
        "codigo_unico": "ONBOARD-003-INVITACION-EQUIPO",
        "categoria": CategoriaNotificacionChoices.ONBOARDING,
        "nombre": "Invitación Miembro Equipo",
        "asunto_email": "👥 {{dueno}} te invita a colaborar en {{negocio}} (ClientBeat)",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "{{dueno}} ({{rol_dueno}}) te ha invitado como {{rol_usuario}} a {{negocio}}.\n"
            "Acepta la invitación: {{invitacion_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:24px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">👥 Nueva invitación a ClientBeat</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <p><strong>{{dueno}}</strong> ({{rol_dueno}}) te ha invitado a <strong>{{negocio}}</strong>.</p>
    <p>Tu rol asignado: <span style="background:#eef4ff;color:#0B3EA6;padding:4px 10px;border-radius:999px;font-weight:700;">{{rol_usuario}}</span></p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{{invitacion_url}}" style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:700;">
        Aceptar Invitación
      </a>
    </div>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "dueno", "rol_dueno", "rol_usuario", "negocio", "invitacion_url"],
        "activo": True,
        "orden": 3,
    },
    {
        "codigo_unico": "ONBOARD-004-PRIMER-QR",
        "categoria": CategoriaNotificacionChoices.ONBOARDING,
        "nombre": "Primer QR Creado Exito",
        "asunto_email": "🎯 ¡Tu primer QR ClientBeat está listo para {{local}}!",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu QR personalizado para {{local}} ya está generado.\n"
            "Descárgalo e imprímelo: {{qr_descarga_url}}\n\n"
            "Cada escaneo = una reseña / encuesta NPS-CSAT.\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:24px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <h2 style="margin:0;">🎯 ¡QR Listo!</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:28px;text-align:center;">
    <p>Tu QR personalizado para <strong>{{local}}</strong> ya está generado.</p>
    <div style="background:#eef4ff;padding:14px;border-radius:10px;margin:20px 0;">
      <p style="margin:0;color:#0B3EA6;font-weight:700;">Cada escaneo = una encuesta NPS / CSAT</p>
    </div>
    <a href="{{qr_descarga_url}}" style="display:inline-block;background:#0B3EA6;color:#fff;padding:14px 30px;border-radius:10px;text-decoration:none;font-weight:700;">
      ⬇️ Descargar PNG / PDF
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "local", "qr_descarga_url"],
        "activo": True,
        "orden": 4,
    },
    # =============================================================
    # CATEGORÍA 2: PLANES (4 plantillas)
    # =============================================================
    {
        "codigo_unico": "PLAN-001-UPGRADE-CONFIRMADO",
        "categoria": CategoriaNotificacionChoices.PLANES,
        "nombre": "Upgrade Plan Confirmado",
        "asunto_email": "⬆️ Upgrade confirmado: ahora estás en {{plan_nuevo}}",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu upgrade de {{plan_anterior}} a {{plan_nuevo}} fue confirmado.\n"
            "Nuevo monto: CLP ${{monto_nuevo}} / mes.\n"
            "Ver factura: {{factura_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:28px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <h1 style="margin:0;font-size:26px;">⬆️ Upgrade Confirmado</h1>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:flex;align-items:center;justify-content:space-between;background:#ecfbf4;border:1px solid #00B879;padding:16px;border-radius:10px;">
      <div style="text-align:center;">
        <div style="color:#6b7280;font-size:12px;">Plan anterior</div>
        <div style="font-weight:700;color:#374151;font-size:18px;">{{plan_anterior}}</div>
      </div>
      <div style="font-size:32px;color:#00B879;">→</div>
      <div style="text-align:center;">
        <div style="color:#6b7280;font-size:12px;">Plan actual</div>
        <div style="font-weight:700;color:#008E5C;font-size:18px;">{{plan_nuevo}}</div>
      </div>
    </div>
    <p style="margin-top:20px;">Nuevo monto: <strong>CLP ${{monto_nuevo}}</strong> / mes</p>
    <a href="{{factura_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      Ver Comprobante
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "plan_anterior", "plan_nuevo", "monto_nuevo", "factura_url"],
        "activo": True,
        "orden": 1,
    },
    {
        "codigo_unico": "PLAN-002-TRIAL-EXPIRA",
        "categoria": CategoriaNotificacionChoices.PLANES,
        "nombre": "Recordatorio Fin Trial",
        "asunto_email": "⏳ Tu período trial termina en {{dias_habiles}} días",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu prueba gratuita de {{negocio}} termina en {{dias_habiles}} días.\n"
            "Selecciona tu plan: {{planes_url}}\n\n"
            "Si no seleccionas, tu cuenta se pausará.\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:28px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <h2 style="margin:0;">⏳ Trial por finalizar</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <p>Tu período trial gratuito de <strong>{{negocio}}</strong> termina en <strong>{{dias_habiles}} días</strong>.</p>
    <p>Selecciona tu plan para continuar accediendo a:</p>
    <ul style="line-height:1.8;">
      <li>✅ QRs NPS/CSAT ilimitados</li>
      <li>✅ Benchmark por rubro</li>
      <li>✅ Notificaciones en tiempo real</li>
    </ul>
    <a href="{{planes_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:14px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:16px;">
      Elegir mi Plan Ahora
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "negocio", "dias_habiles", "planes_url"],
        "activo": True,
        "orden": 2,
    },
    {
        "codigo_unico": "PLAN-003-CAMBIO-DOWNGRADE",
        "categoria": CategoriaNotificacionChoices.PLANES,
        "nombre": "Downgrade Plan Informado",
        "asunto_email": "📉 Cambio de plan procesado: {{plan_nuevo}}",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu cambio a {{plan_nuevo}} ha sido procesado.\n"
            "Entra en vigencia: {{fecha_vigencia}}.\n"
            "Revisa tus features: {{planes_comparativo_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:24px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">📉 Cambio de plan confirmado</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:28px;">
    <p>Hola <strong>{{usuario}}</strong>, tu cambio de plan fue procesado exitosamente:</p>
    <div style="background:#eef4ff;padding:16px;border-radius:10px;">
      <p style="margin:0 0 8px 0;">Nuevo plan: <strong>{{plan_nuevo}}</strong></p>
      <p style="margin:0;">Fecha vigencia: <strong>{{fecha_vigencia}}</strong></p>
    </div>
    <a href="{{planes_comparativo_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      Comparar Features
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "plan_nuevo", "fecha_vigencia", "planes_comparativo_url"],
        "activo": True,
        "orden": 3,
    },
    {
        "codigo_unico": "PLAN-004-RENOVACION-AUTOMATICA",
        "categoria": CategoriaNotificacionChoices.PLANES,
        "nombre": "Renovación Automática Próxima",
        "asunto_email": "🔁 Tu suscripción se renueva en {{dias_renovacion}} días",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu plan {{plan}} se renueva automáticamente el {{fecha_renovacion}}.\n"
            "Monto: ${{monto}} CLP.\n\nGestionar suscripción: {{suscripcion_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:24px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">🔁 Próxima renovación automática</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:28px;">
    <p>Hola <strong>{{usuario}}</strong>,</p>
    <div style="background:#eef4ff;border:1px solid #d9e7ff;padding:16px;border-radius:10px;margin:20px 0;">
      <p style="margin:0 0 8px 0;">📅 <strong>{{fecha_renovacion}}</strong></p>
      <p style="margin:0 0 8px 0;">Plan: <strong>{{plan}}</strong></p>
      <p style="margin:0;">🔐 Monto a cargar: <strong>${{monto}} CLP</strong></p>
    </div>
    <a href="{{suscripcion_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;">
      Gestionar Suscripción
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "plan", "fecha_renovacion", "monto", "dias_renovacion", "suscripcion_url"],
        "activo": True,
        "orden": 4,
    },
    # =============================================================
    # CATEGORÍA 3: PAGOS (4 plantillas)
    # =============================================================
    {
        "codigo_unico": "PAGO-001-EXITOSO",
        "categoria": CategoriaNotificacionChoices.PAGOS,
        "nombre": "Pago Exitoso Factura",
        "asunto_email": "✅ Pago Aprobado – Factura {{numero_factura}}",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu pago de ${{monto}} CLP fue aprobado.\n"
            "Factura: {{numero_factura}}\n"
            "Descargar PDF: {{pdf_factura_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:32px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <div style="font-size:48px;">✅</div>
    <h2 style="margin:8px 0 0 0;">¡Pago Aprobado!</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="background:#ecfbf4;border:1px solid #00B879;border-radius:10px;padding:16px;">
      <p style="margin:4px 0;">🧾 Comprobante N°: <strong>{{numero_factura}}</strong></p>
      <p style="margin:4px 0;">💲 Monto: <strong>${{monto}} CLP</strong></p>
      <p style="margin:4px 0;">📅 Fecha: <strong>{{fecha_pago}}</strong></p>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="{{pdf_factura_url}}" style="background:#0B3EA6;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:700;">
        📄 Descargar Comprobante PDF
      </a>
    </div>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "numero_factura", "monto", "fecha_pago", "pdf_factura_url"],
        "activo": True,
        "orden": 1,
    },
    {
        "codigo_unico": "PAGO-002-FALLIDO",
        "categoria": CategoriaNotificacionChoices.PAGOS,
        "nombre": "Pago Fallido Reintento",
        "asunto_email": "⚠️ Tu pago no pudo procesarse – intenta nuevamente",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu pago de ${{monto}} CLP no pudo ser procesado.\n"
            "Motivo: {{motivo}}\n"
            "Actualiza tu medio de pago: {{metodo_pago_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#041B3A 100%);padding:28px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <div style="font-size:40px;">⚠️</div>
    <h2 style="margin:8px 0 0 0;">Pago no procesado</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <p>Hola <strong>{{usuario}}</strong>,</p>
    <p>No pudimos procesar tu pago de <strong>${{monto}} CLP</strong>.</p>
    <div style="background:#eef4ff;border-left:4px solid #0B3EA6;padding:12px 16px;border-radius:6px;">
      <p style="margin:0;"><strong>Motivo:</strong> {{motivo}}</p>
    </div>
    <a href="{{metodo_pago_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      Actualizar Medio de Pago
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "monto", "motivo", "metodo_pago_url"],
        "activo": True,
        "orden": 2,
    },
    {
        "codigo_unico": "PAGO-003-CUENTA-ATRASADA",
        "categoria": CategoriaNotificacionChoices.PAGOS,
        "nombre": "Cuenta Morosa Atrasada",
        "asunto_email": "🚨 Tu cuenta ClientBeat está atrasada {{dias_atraso}} días",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu cuenta está atrasada {{dias_atraso}} días por ${{monto_deuda}} CLP.\n"
            "Sin pago, el acceso se suspenderá el {{fecha_suspension}}.\n"
            "Regulariza ahora: {{pagar_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#041B3A 100%);color:#fff;padding:22px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">🚨 Cuenta en Período de Gracia</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:28px;">
    <p>Tu cuenta de <strong>{{negocio}}</strong> presenta <strong>{{dias_atraso}} días</strong> de atraso.</p>
    <div style="background:#eef4ff;padding:16px;border-radius:10px;margin:16px 0;border-left:4px solid #0B3EA6;">
      <p style="margin:0 0 8px 0;">💲 Monto pendiente: <strong>${{monto_deuda}} CLP</strong></p>
      <p style="margin:0;">⏰ Suspensión programada: <strong>{{fecha_suspension}}</strong></p>
    </div>
    <a href="{{pagar_url}}" style="display:block;text-align:center;background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:14px;border-radius:10px;text-decoration:none;font-weight:700;">
      Regularizar Pago Ahora
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "negocio", "dias_atraso", "monto_deuda", "fecha_suspension", "pagar_url"],
        "activo": True,
        "orden": 3,
    },
    {
        "codigo_unico": "PAGO-004-REEMBOLSO",
        "categoria": CategoriaNotificacionChoices.PAGOS,
        "nombre": "Solicitud Reembolso Confirmada",
        "asunto_email": "↩️ Solicitud de reembolso N° {{numero_reembolso}} confirmada",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu solicitud de reembolso por ${{monto}} CLP fue confirmada.\n"
            "Monto: ${{monto}} CLP\n"
            "Fecha depósito estimado: {{fecha_estimada}}\n\n"
            "Seguimiento: {{seguimiento_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">↩️ Reembolso Confirmado</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:28px;">
    <p>Hola <strong>{{usuario}}</strong>, tu solicitud fue ingresada exitosamente.</p>
    <div style="background:#eef4ff;padding:16px;border-radius:10px;margin:20px 0;">
      <p style="margin:4px 0;">🧾 N° Solicitud: <strong>{{numero_reembolso}}</strong></p>
      <p style="margin:4px 0;">💲 Monto: <strong>${{monto}} CLP</strong></p>
      <p style="margin:4px 0;">📅 Depósito estimado: <strong>{{fecha_estimada}}</strong></p>
    </div>
    <a href="{{seguimiento_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;">
      Ver Seguimiento
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "numero_reembolso", "monto", "fecha_estimada", "seguimiento_url"],
        "activo": True,
        "orden": 4,
    },
    # =============================================================
    # CATEGORÍA 4: BENCHMARK (4 plantillas)
    # =============================================================
    {
        "codigo_unico": "BENCH-001-REPORTE-SEMANAL",
        "categoria": CategoriaNotificacionChoices.BENCHMARK,
        "nombre": "Reporte Benchmark Semanal",
        "asunto_email": "📊 Tu benchmark semanal {{semana}}: NPS {{nps_score}} vs Rubro {{nps_rubro}}",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu negocio {{negocio}} ({{rubro}}) tuvo esta semana:\n"
            "• NPS: {{nps_score}} (Rubro promedio: {{nps_rubro}})\n"
            "• CSAT: {{csat_indice}}% (Rubro promedio: {{csat_rubro}}%)\n"
            "• Posición: Top {{posicion_percentil}}% en {{region}}\n\n"
            "Ver reporte completo: {{reporte_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6,#00B879);padding:28px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">📊 Reporte Benchmark Semanal</h2>
    <p style="opacity:0.95;margin-top:6px;">{{negocio}} · {{rubro}} · Semana {{semana}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div style="background:#eef4ff;padding:16px;border-radius:10px;text-align:center;">
        <div style="font-size:12px;color:#6b7280;">NPS Tú</div>
        <div style="font-size:32px;font-weight:800;color:#0B3EA6;">{{nps_score}}</div>
        <div style="font-size:11px;color:#08337a;margin-top:4px;">Rubro: {{nps_rubro}}</div>
      </div>
      <div style="background:#ecfbf4;padding:16px;border-radius:10px;text-align:center;">
        <div style="font-size:12px;color:#6b7280;">CSAT Tú</div>
        <div style="font-size:32px;font-weight:800;color:#00B879;">{{csat_indice}}%</div>
        <div style="font-size:11px;color:#008E5C;margin-top:4px;">Rubro: {{csat_rubro}}%</div>
      </div>
    </div>
    <p style="margin-top:20px;">Estás en el <strong>Top {{posicion_percentil}}%</strong> de {{region}}.</p>
    <a href="{{reporte_url}}" style="display:block;text-align:center;background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      Ver Reporte Completo →
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "negocio", "rubro", "semana", "nps_score", "nps_rubro", "csat_indice", "csat_rubro", "posicion_percentil", "region", "reporte_url"],
        "activo": True,
        "orden": 1,
    },
    {
        "codigo_unico": "BENCH-002-COMPETENCIA-NUEVA-RESEÑA",
        "categoria": CategoriaNotificacionChoices.BENCHMARK,
        "nombre": "Nueva Reseña Competencia",
        "asunto_email": "🏁 {{competencia}} recibió una reseña de {{estrellas}}⭐ hace {{tiempo_minutos}}min",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu competidor {{competencia}} acaba de recibir una reseña.\n"
            "⭐ {{estrellas}}/5\n"
            "Texto: {{texto_resena}}\n\n"
            "Analizar en Dashboard: {{competencia_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:22px;border-radius:14px 14px 0 0;color:#fff;">
    <h3 style="margin:0;">🏁 Actividad de Competencia</h3>
    <p style="margin:4px 0 0 0;opacity:0.9;">{{competencia}} · hace {{tiempo_minutos}} min</p>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:24px;">
    <div style="background:#eef4ff;padding:16px;border-radius:10px;">
      <div style="font-size:22px;color:#0B3EA6;">
        {% for i in ''|ljust:estrellas %}⭐{% endfor %}
      </div>
      <p style="margin-top:8px;line-height:1.5;">{{texto_resena}}</p>
    </div>
    <a href="{{competencia_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      Ver Análisis Competencia
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "competencia", "estrellas", "tiempo_minutos", "texto_resena", "competencia_url"],
        "activo": True,
        "orden": 2,
    },
    {
        "codigo_unico": "BENCH-003-RANKING-SUBE",
        "categoria": CategoriaNotificacionChoices.BENCHMARK,
        "nombre": "Subiste en Ranking Rubro",
        "asunto_email": "🚀 ¡Subiste {{posiciones_subidas}} puestos en el ranking de {{rubro}}!",
        "cuerpo_texto_plano": (
            "¡Felicidades {{usuario}}!\n\n"
            "{{negocio}} subió {{posiciones_subidas}} puestos y ahora es N° {{posicion_actual}} en {{comuna}}.\n\n"
            "Ver ranking: {{ranking_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6,#00B879);padding:28px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <div style="font-size:56px;">🚀</div>
    <h2 style="margin:8px 0 0 0;">¡Subiste {{posiciones_subidas}} puestos!</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;text-align:center;">
    <p>Hola <strong>{{usuario}}</strong>, <strong>{{negocio}}</strong> lo está haciendo genial:</p>
    <div style="background:#ecfbf4;border:2px solid #00B879;padding:20px;border-radius:12px;margin:20px 0;display:inline-block;">
      <div style="font-size:14px;color:#008E5C;">Ahora eres el</div>
      <div style="font-size:60px;font-weight:900;color:#0B3EA6;line-height:1;">N° {{posicion_actual}}</div>
      <div style="font-size:14px;color:#008E5C;margin-top:4px;">de {{rubro}} en {{comuna}}</div>
    </div>
    <div>
      <a href="{{ranking_url}}" style="display:inline-block;background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:700;">
        Ver Ranking Completo
      </a>
    </div>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "negocio", "posiciones_subidas", "posicion_actual", "rubro", "comuna", "ranking_url"],
        "activo": True,
        "orden": 3,
    },
    {
        "codigo_unico": "BENCH-004-ALERTA-RATING",
        "categoria": CategoriaNotificacionChoices.BENCHMARK,
        "nombre": "Alerta Rating Google vs Competencia",
        "asunto_email": "⚠️ {{competidor}} te supera en Google Rating por {{diferencia}}⭐",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Alerta de rating:\n"
            "• Tú: {{tu_rating}}⭐ ({{tu_cantidad}} reseñas)\n"
            "• {{competidor}}: {{competidor_rating}}⭐ ({{competidor_cantidad}} reseñas)\n"
            "Diferencia: {{diferencia}} estrellas.\n\n"
            "Generar reseñas con QR: {{qr_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6,#041B3A);color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">⚠️ Alerta Rating Competencia</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0;">
      <div style="background:#eef4ff;padding:16px;border-radius:10px;border:1px solid #d9e7ff;text-align:center;">
        <div style="font-size:12px;color:#0B3EA6;font-weight:700;">TÚ</div>
        <div style="font-size:36px;font-weight:800;color:#0B3EA6;">{{tu_rating}}⭐</div>
        <div style="font-size:12px;color:#08337a;">{{tu_cantidad}} reseñas</div>
      </div>
      <div style="background:#ecfbf4;padding:16px;border-radius:10px;border:1px solid #00B879;text-align:center;">
        <div style="font-size:12px;color:#008E5C;font-weight:700;">COMPETENCIA</div>
        <div style="font-size:36px;font-weight:800;color:#008E5C;">{{competidor_rating}}⭐</div>
        <div style="font-size:12px;color:#008E5C;">{{competidor_cantidad}} reseñas</div>
      </div>
    </div>
    <p style="text-align:center;">Diferencia actual: <strong>{{diferencia}} estrellas</strong></p>
    <a href="{{qr_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:16px;">
      Generar + Reseñas con QR →
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "competidor", "tu_rating", "tu_cantidad", "competidor_rating", "competidor_cantidad", "diferencia", "qr_url"],
        "activo": True,
        "orden": 4,
    },
    # =============================================================
    # CATEGORÍA 5: CSAT / NPS y Encuestas (4 plantillas)
    # =============================================================
    {
        "codigo_unico": "NPS-001-DETRACTOR-ALERTA",
        "categoria": CategoriaNotificacionChoices.CSAT_NPS,
        "nombre": "Alerta Respuesta Detractor NPS",
        "asunto_email": "🚨 NPS Detractor ({{puntaje}}/10) en {{local}} – {{cliente_nombre}}",
        "cuerpo_texto_plano": (
            "Alerta inmediata {{usuario}}:\n\n"
            "{{cliente_nombre}} respondió NPS {{puntaje}}/10 en {{local}}.\n"
            "Motivo: {{comentario}}\n"
            "Responder al cliente: {{responder_url}}\n\n"
            "Tiempo recomendado: < 1 hora.\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#041B3A 100%);color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">🚨 Alerta NPS Detractor</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">{{local}} · hace {{tiempo}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div>
        <div style="font-size:12px;color:#6b7280;">Cliente</div>
        <div style="font-weight:700;color:#041B3A;">{{cliente_nombre}}</div>
      </div>
      <div style="text-align:center;background:#eef4ff;border:2px solid #0B3EA6;padding:8px 16px;border-radius:10px;">
        <div style="font-size:28px;font-weight:900;color:#0B3EA6;line-height:1;">{{puntaje}}</div>
        <div style="font-size:11px;color:#08337a;">/ 10</div>
      </div>
    </div>
    <div style="background:#eef4ff;padding:14px;border-radius:8px;border-left:4px solid #0B3EA6;">
      <p style="margin:0;line-height:1.5;">💬 {{comentario}}</p>
    </div>
    <a href="{{responder_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      📨 Gestionar en Dashboard (< 1 hora)
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "cliente_nombre", "puntaje", "local", "comentario", "tiempo", "responder_url"],
        "activo": True,
        "orden": 1,
    },
    {
        "codigo_unico": "NPS-002-PROMOTOR-AGRADECIMIENTO",
        "categoria": CategoriaNotificacionChoices.CSAT_NPS,
        "nombre": "Nuevo Promotor NPS (sugerir reseña G)",
        "asunto_email": "💚 ¡Nuevo Promotor NPS {{puntaje}}/10! Pide una reseña Google a {{cliente_nombre}}",
        "cuerpo_texto_plano": (
            "¡Genial {{usuario}}!\n\n"
            "{{cliente_nombre}} calificó {{puntaje}}/10 en {{local}}.\n"
            "Comentario: {{comentario}}\n\n"
            "Aprovecha y pide una reseña Google: {{pedir_resena_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">💚 ¡Promotor NPS!</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">Oportunidad de reseña Google 👀</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div>
        <div style="font-size:12px;color:#6b7280;">Cliente</div>
        <div style="font-weight:700;color:#041B3A;">{{cliente_nombre}}</div>
      </div>
      <div style="text-align:center;background:#ecfbf4;border:2px solid #00B879;padding:8px 16px;border-radius:10px;">
        <div style="font-size:28px;font-weight:900;color:#008E5C;line-height:1;">{{puntaje}}</div>
        <div style="font-size:11px;color:#00633F;">/ 10 PROMOTOR</div>
      </div>
    </div>
    <div style="background:#ecfbf4;padding:14px;border-radius:8px;border-left:4px solid #00B879;">
      <p style="margin:0;line-height:1.5;">💬 {{comentario}}</p>
    </div>
    <a href="{{pedir_resena_url}}" style="display:block;text-align:center;background:#00B879;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      Pedir Reseña Google 🌟
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "cliente_nombre", "puntaje", "local", "comentario", "pedir_resena_url"],
        "activo": True,
        "orden": 2,
    },
    {
        "codigo_unico": "CSAT-001-RESUMEN-DIARIO",
        "categoria": CategoriaNotificacionChoices.CSAT_NPS,
        "nombre": "Resumen Diario CSAT + NPS",
        "asunto_email": "📈 Resumen diario: {{total_respuestas}} respuestas · NPS {{nps_diario}} · CSAT {{csat_diario}}%",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Resumen {{fecha}}:\n"
            "• Respuestas totales: {{total_respuestas}}\n"
            "• NPS día: {{nps_diario}} ({{promotores}}P / {{pasivos}}Pa / {{detractores}}D)\n"
            "• CSAT promedio: {{csat_diario}}%\n"
            "• Mejor local: {{mejor_local}} (NPS {{mejor_nps}})\n\n"
            "Ver dashboard: {{dashboard_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:26px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">📈 Resumen Diario · {{fecha}}</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">{{negocio}}</p>
  </div>
  <div style="background:#fff;padding:24px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0;">
      <div style="text-align:center;background:#f8fafc;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#6b7280;">RESPUESTAS</div>
        <div style="font-size:28px;font-weight:800;color:#041B3A;">{{total_respuestas}}</div>
      </div>
      <div style="text-align:center;background:#eef4ff;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#0B3EA6;">NPS HOY</div>
        <div style="font-size:28px;font-weight:800;color:#0B3EA6;">{{nps_diario}}</div>
      </div>
      <div style="text-align:center;background:#ecfbf4;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#008E5C;">CSAT</div>
        <div style="font-size:28px;font-weight:800;color:#00B879;">{{csat_diario}}%</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:12px 0;">
      <div style="text-align:center;background:#ecfbf4;padding:10px;border-radius:8px;">
        <div style="font-size:11px;color:#008E5C;">PROMOTORES</div>
        <div style="font-weight:800;color:#008E5C;">{{promotores}}</div>
      </div>
      <div style="text-align:center;background:#eef4ff;padding:10px;border-radius:8px;">
        <div style="font-size:11px;color:#0B3EA6;">PASIVOS</div>
        <div style="font-weight:800;color:#0B3EA6;">{{pasivos}}</div>
      </div>
      <div style="text-align:center;background:#f1f5f9;padding:10px;border-radius:8px;">
        <div style="font-size:11px;color:#041B3A;">DETRACTORES</div>
        <div style="font-weight:800;color:#041B3A;">{{detractores}}</div>
      </div>
    </div>
    <p>🏆 Mejor local: <strong>{{mejor_local}}</strong> (NPS {{mejor_nps}})</p>
    <a href="{{dashboard_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:16px;">
      Abrir Dashboard
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "negocio", "fecha", "total_respuestas", "nps_diario", "csat_diario", "promotores", "pasivos", "detractores", "mejor_local", "mejor_nps", "dashboard_url"],
        "activo": True,
        "orden": 3,
    },
    {
        "codigo_unico": "ENCUESTA-001-NUEVA-PREGUNTA-CUSTOM",
        "categoria": CategoriaNotificacionChoices.CSAT_NPS,
        "nombre": "Encuesta Custom Rubro Activada",
        "asunto_email": "📝 Encuesta específica {{rubro}} activada en {{local}}",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Tu encuesta custom de {{rubro}} ya está activa.\n"
            "Nuevas preguntas: {{cantidad_preguntas}} preguntas adicionales.\n"
            "Previsualizar encuesta: {{preview_url}}\n\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:24px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">📝 Encuesta Custom Activada</h2>
  </div>
  <div style="background:#fff;border:1px solid #d9e7ff;border-top:none;padding:28px;">
    <p>Rubro <strong>{{rubro}}</strong> · Local <strong>{{local}}</strong></p>
    <div style="background:#eef4ff;padding:16px;border-radius:10px;margin:16px 0;">
      <p style="margin:0;">✅ Preguntas base NPS + CSAT</p>
      <p style="margin:8px 0 0 0;">➕ <strong>{{cantidad_preguntas}}</strong> preguntas específicas rubro</p>
    </div>
    <a href="{{preview_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;">
      🔍 Previsualizar Encuesta
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "rubro", "local", "cantidad_preguntas", "preview_url"],
        "activo": True,
        "orden": 4,
    },
    # =============================================================
    # CATEGORÍA 6: RESEÑAS GOOGLE (4 plantillas)
    # =============================================================
    {
        "codigo_unico": "G-RESEÑA-001-NUEVA-CALIFICADA",
        "categoria": CategoriaNotificacionChoices.RESEÑAS_GOOGLE,
        "nombre": "Nueva Reseña Google Calificada",
        "asunto_email": "🌟 Nueva reseña Google {{estrellas}}⭐ en {{local}} – Respóndela!",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Nueva reseña Google en {{local}}:\n"
            "{{estrellas}}/5 - {{autor}}\n"
            "{{comentario}}\n\n"
            "Responder en Google (Tiempo recomendado < 24h): {{responder_g_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">🌟 Nueva Reseña Google</h2>
    <p style="margin:6px 0 0 0;">{{local}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">
      <div style="width:52px;height:52px;background:#eef4ff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#0B3EA6;">
        {{autor|first|upper}}
      </div>
      <div style="flex:1;">
        <div style="font-weight:700;color:#041B3A;">{{autor}}</div>
        <div style="color:#00B879;font-weight:700;">
          {% for s in ''|ljust:estrellas %}⭐{% endfor %}
          <span style="color:#6b7280;">{{estrellas}}.0</span>
        </div>
      </div>
    </div>
    <div style="background:#eef4ff;padding:14px;border-radius:10px;border-left:4px solid #0B3EA6;">
      <p style="margin:0;line-height:1.5;">{{comentario}}</p>
    </div>
    <a href="{{responder_g_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:20px;">
      💬 Responder en Google (< 24h)
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "estrellas", "local", "autor", "comentario", "responder_g_url"],
        "activo": True,
        "orden": 1,
    },
    {
        "codigo_unico": "G-RESEÑA-002-SIN-RESPONDER-48H",
        "categoria": CategoriaNotificacionChoices.RESEÑAS_GOOGLE,
        "nombre": "Recordatorio Reseña sin Responder 48h",
        "asunto_email": "⏰ Reseña Google de {{autor}} pendiente +48h en {{local}}",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "La reseña de {{autor}} ({{estrellas}}⭐) en {{local}} lleva 48 horas sin respuesta.\n"
            "Responder antes de 72h mejora tu ranking SEO local.\n\n"
            "Responder: {{responder_g_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#041B3A 100%);color:#fff;padding:22px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">⏰ Reseña sin responder (+48h)</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="background:#eef4ff;padding:14px;border-left:4px solid #0B3EA6;border-radius:6px;margin-bottom:16px;">
      <p style="margin:0;">💡 Responder reseñas antes de 72h mejora tu <strong>SEO local Google</strong> y tu rating percibido.</p>
    </div>
    <p>De <strong>{{autor}}</strong> · {{estrellas}}⭐ en <strong>{{local}}</strong></p>
    <a href="{{responder_g_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:16px;">
      Responder Ahora
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "autor", "estrellas", "local", "responder_g_url"],
        "activo": True,
        "orden": 2,
    },
    {
        "codigo_unico": "G-RESEÑA-003-PROMEDIO-ALCANZA-4.5",
        "categoria": CategoriaNotificacionChoices.RESEÑAS_GOOGLE,
        "nombre": "Meta Rating Alcanzado (ej: 4.5⭐)",
        "asunto_email": "🎯 ¡Meta alcanzada! Rating Google de {{local}} ahora es {{rating_nuevo}}⭐",
        "cuerpo_texto_plano": (
            "¡Felicidades {{usuario}}!\n\n"
            "Tu local {{local}} alcanzó {{rating_nuevo}}⭐ promedio en Google.\n"
            "Total reseñas: {{total_resenas}}\n\n"
            "Sigue así: {{pedir_qr_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6,#00B879);padding:30px;border-radius:14px 14px 0 0;color:#fff;text-align:center;">
    <div style="font-size:56px;">🎯</div>
    <h1 style="margin:10px 0 0 0;">¡Rating Meta Alcanzada!</h1>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;text-align:center;">
    <p>Hola <strong>{{usuario}}</strong>, lo lograste en <strong>{{local}}</strong>:</p>
    <div style="display:inline-block;background:#ecfbf4;border:2px solid #00B879;padding:24px;border-radius:14px;margin:20px 0;">
      <div style="font-size:12px;color:#008E5C;font-weight:700;">RATING ACTUAL</div>
      <div style="font-size:64px;font-weight:900;color:#0B3EA6;line-height:1;">{{rating_nuevo}}⭐</div>
      <div style="font-size:13px;color:#008E5C;margin-top:4px;">{{total_resenas}} reseñas totales</div>
    </div>
    <div>
      <a href="{{pedir_qr_url}}" style="display:inline-block;background:#00B879;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:700;">
        Pedir Más Reseñas con QR →
      </a>
    </div>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "local", "rating_nuevo", "total_resenas", "pedir_qr_url"],
        "activo": True,
        "orden": 3,
    },
    {
        "codigo_unico": "G-RESEÑA-004-REPORTAJE-MENSUAL",
        "categoria": CategoriaNotificacionChoices.RESEÑAS_GOOGLE,
        "nombre": "Reporte Mensual Reseñas Google",
        "asunto_email": "📅 Reportaje Google {{mes}}: +{{cantidad_nuevas}} reseñas · Rating {{rating_actual}}⭐",
        "cuerpo_texto_plano": (
            "Hola {{usuario}},\n\n"
            "Reporte Google {{mes}} {{negocio}}:\n"
            "• Nuevas reseñas: +{{cantidad_nuevas}}\n"
            "• Rating actual: {{rating_actual}}⭐ (anterior: {{rating_anterior}}⭐)\n"
            "• Reseñas respondidas: {{respondidas}}/{{cantidad_nuevas}} ({{tasa_respuesta}}%)\n\n"
            "Ver todas: {{dashboard_url}}\nEquipo ClientBeat · contactoclientbeat@gmail.com"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;font-family:Arial,sans-serif;">
  <div style="background:linear-gradient(135deg,#0B3EA6 0%,#00B879 100%);padding:26px;border-radius:14px 14px 0 0;color:#fff;">
    <h2 style="margin:0;">📅 Reporte Mensual Google</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">{{mes}} · {{negocio}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #d9e7ff;border-top:none;">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0;">
      <div style="text-align:center;background:#eef4ff;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#0B3EA6;">NUEVAS</div>
        <div style="font-size:30px;font-weight:800;color:#0B3EA6;">+{{cantidad_nuevas}}</div>
      </div>
      <div style="text-align:center;background:#f8fafc;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#041B3A;">RATING</div>
        <div style="font-size:30px;font-weight:800;color:#041B3A;">{{rating_actual}}⭐</div>
        <div style="font-size:10px;color:#64748b;">antes {{rating_anterior}}⭐</div>
      </div>
      <div style="text-align:center;background:#ecfbf4;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#008E5C;">TASA RESPUESTA</div>
        <div style="font-size:30px;font-weight:800;color:#00B879;">{{tasa_respuesta}}%</div>
        <div style="font-size:10px;color:#00633F;">{{respondidas}}/{{cantidad_nuevas}}</div>
      </div>
    </div>
    <a href="{{dashboard_url}}" style="display:block;text-align:center;background:#0B3EA6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:16px;">
      Ver Reseñas en Dashboard
    </a>
  </div>
  <div style="background:#041B3A;padding:18px 24px;text-align:center;border-radius:0 0 14px 14px;">
    <p style="font-size:12px;color:#d9e7ff;margin:0;">ClientBeat SpA · Soporte: <a href="mailto:contactoclientbeat@gmail.com" style="color:#00B879;text-decoration:none;font-weight:700;">contactoclientbeat@gmail.com</a></p>
  </div>
</div>
        """,
        "variables_esperadas": ["usuario", "mes", "negocio", "cantidad_nuevas", "rating_actual", "rating_anterior", "respondidas", "tasa_respuesta", "dashboard_url"],
        "activo": True,
        "orden": 4,
    },
]


class Command(BaseCommand):
    help = "Carga 24 plantillas de notificaciones (6 categorías × 4) en NeonDB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina todas las plantillas antes de insertar (DELETE CASCADE).",
        )

    def handle(self, *args, **options):
        reset = options["reset"]
        ahora = timezone.now()

        if reset:
            total_borrados, _ = PlantillaNotificacion.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"🧹 [RESET] Borradas {total_borrados} plantillas preexistentes.")
            )

        creadas = 0
        actualizadas = 0
        categorias_count = {c[0]: 0 for c in CategoriaNotificacionChoices.choices}

        for idx, data in enumerate(PLANTILLAS, start=1):
            codigo = data["codigo_unico"]
            obj, created = PlantillaNotificacion.objects.update_or_create(
                codigo_unico=codigo,
                defaults={
                    "categoria": data["categoria"],
                    "nombre": data["nombre"],
                    "asunto_email": data["asunto_email"],
                    "cuerpo_texto_plano": data["cuerpo_texto_plano"],
                    "cuerpo_html": data["cuerpo_html"].strip(),
                    "variables_esperadas": data["variables_esperadas"],
                    "activo": data["activo"],
                    "orden": data["orden"],
                },
            )
            categorias_count[data["categoria"]] += 1
            if created:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ [{idx}] CREATE {codigo}"))
            else:
                actualizadas += 1
                self.stdout.write(self.style.SQL_COLTYPE(f"  🔄 [{idx}] UPDATE {codigo}"))

        # Resumen final
        total_db = PlantillaNotificacion.objects.count()
        activas_db = PlantillaNotificacion.objects.filter(activo=True).count()

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(self.style.MIGRATE_HEADING("  📬 RESUMEN SEED NOTIFICACIONES PLANTILLAS"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(f"  🆕 Creadas esta ejecución  : {creadas}")
        self.stdout.write(f"  🔄 Actualizadas           : {actualizadas}")
        self.stdout.write(f"  📊 Total en DB            : {total_db}")
        self.stdout.write(f"  ✅ Activas                : {activas_db}")
        self.stdout.write(self.style.MIGRATE_HEADING("  --- Distribución por categoría ---"))
        for cat_key, cat_label in CategoriaNotificacionChoices.choices:
            self.stdout.write(f"     • {cat_label:<30} : {categorias_count[cat_key]:>2} plantillas")
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ seed_notificaciones finalizado OK @ {ahora.isoformat(timespec='seconds')}"
            )
        )
