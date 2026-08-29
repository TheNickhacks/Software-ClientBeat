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
            "Cordialmente,\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;font-family:Arial,sans-serif;color:#1f2937;">
  <div style="background:linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%);padding:32px;text-align:center;color:#fff;border-radius:16px 16px 0 0;">
    <h1 style="margin:0;font-size:28px;">🎉 ¡Bienvenido a ClientBeat!</h1>
    <p style="opacity:0.95;margin-top:8px;">Hola {{usuario}}, gracias por elegirnos.</p>
  </div>
  <div style="background:#fff;padding:32px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 16px 16px;">
    <p style="font-size:16px;line-height:1.6;">Tu negocio <strong>{{negocio}}</strong> ya está registrado con el plan <strong>{{plan}}</strong>.</p>
    <p style="font-size:16px;line-height:1.6;">Siguientes pasos sugeridos:</p>
    <ol style="font-size:16px;line-height:1.8;">
      <li>Configura tus <strong>locales y QR</strong></li>
      <li>Personaliza la <strong>identidad visual</strong></li>
      <li>Invita a tu <strong>equipo</strong></li>
    </ol>
    <div style="text-align:center;margin-top:28px;">
      <a href="{{dashboard_url}}" style="display:inline-block;background:#4F46E5;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:600;">
        Ir al Dashboard →
      </a>
    </div>
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
            "Si no solicitaste esto, ignóralo.\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:560px;margin:0 auto;">
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:32px;">
    <h2 style="color:#4F46E5;margin-top:0;">📩 Confirma tu correo</h2>
    <p>Hola <strong>{{usuario}}</strong>,</p>
    <p>Por favor confirma tu email para completar el registro:</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{{confirmacion_url}}" style="background:#10B981;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:600;">
        ✅ Confirmar Email
      </a>
    </div>
    <p style="font-size:13px;color:#6b7280;">O copia y pega: {{confirmacion_url}}</p>
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
            "Acepta la invitación: {{invitacion_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#06B6D4,#4F46E5);padding:24px;border-radius:14px;color:#fff;">
    <h2 style="margin:0;">👥 Nueva invitación</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <p><strong>{{dueno}}</strong> ({{rol_dueno}}) te ha invitado a <strong>{{negocio}}</strong>.</p>
    <p>Tu rol asignado: <span style="background:#EEF2FF;color:#4F46E5;padding:4px 10px;border-radius:999px;">{{rol_usuario}}</span></p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{{invitacion_url}}" style="background:#4F46E5;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:600;">
        Aceptar Invitación
      </a>
    </div>
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
            "Cada escaneo = una reseña / encuesta NPS-CSAT.\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:2px dashed #7C3AED;border-radius:16px;padding:28px;text-align:center;">
    <h2 style="color:#7C3AED;margin-top:0;">🎯 ¡QR Listo!</h2>
    <p>Tu QR personalizado para <strong>{{local}}</strong> ya está generado.</p>
    <div style="background:#f5f3ff;padding:14px;border-radius:10px;margin:20px 0;">
      <p style="margin:0;color:#4F46E5;font-weight:600;">Cada escaneo = una encuesta NPS / CSAT</p>
    </div>
    <a href="{{qr_descarga_url}}" style="display:inline-block;background:#7C3AED;color:#fff;padding:14px 30px;border-radius:10px;text-decoration:none;font-weight:600;">
      ⬇️ Descargar PNG / PDF
    </a>
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
            "Ver factura: {{factura_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#10B981 0%,#059669 100%);padding:28px;border-radius:14px;color:#fff;text-align:center;">
    <h1 style="margin:0;font-size:26px;">⬆️ Upgrade Confirmado</h1>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:flex;align-items:center;justify-content:space-between;background:#f0fdf4;border:1px solid #bbf7d0;padding:16px;border-radius:10px;">
      <div style="text-align:center;">
        <div style="color:#6b7280;font-size:12px;">Plan anterior</div>
        <div style="font-weight:700;color:#374151;font-size:18px;">{{plan_anterior}}</div>
      </div>
      <div style="font-size:32px;color:#10B981;">→</div>
      <div style="text-align:center;">
        <div style="color:#6b7280;font-size:12px;">Plan actual</div>
        <div style="font-weight:700;color:#059669;font-size:18px;">{{plan_nuevo}}</div>
      </div>
    </div>
    <p style="margin-top:20px;">Nuevo monto: <strong>CLP ${{monto_nuevo}}</strong> / mes</p>
    <a href="{{factura_url}}" style="display:block;text-align:center;background:#4F46E5;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      Ver Factura
    </a>
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
            "Si no seleccionas, tu cuenta se pausará.\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#F59E0B,#D97706);padding:28px;border-radius:14px;color:#fff;text-align:center;">
    <h2 style="margin:0;">⏳ Trial por finalizar</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <p>Tu período trial gratuito de <strong>{{negocio}}</strong> termina en <strong>{{dias_habiles}} días</strong>.</p>
    <p>Selecciona tu plan para continuar accediendo a:</p>
    <ul style="line-height:1.8;">
      <li>✅ QRs NPS/CSAT ilimitados</li>
      <li>✅ Benchmark por rubro</li>
      <li>✅ Notificaciones en tiempo real</li>
    </ul>
    <a href="{{planes_url}}" style="display:block;text-align:center;background:#F59E0B;color:#fff;padding:14px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:16px;">
      Elegir mi Plan Ahora
    </a>
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
            "Revisa tus features: {{planes_comparativo_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:28px;">
    <h2 style="color:#4F46E5;margin-top:0;">📉 Cambio de plan confirmado</h2>
    <p>Hola <strong>{{usuario}}</strong>, tu cambio de plan fue procesado exitosamente:</p>
    <div style="background:#f3f4f6;padding:16px;border-radius:10px;">
      <p style="margin:0 0 8px 0;">Nuevo plan: <strong>{{plan_nuevo}}</strong></p>
      <p style="margin:0;">Fecha vigencia: <strong>{{fecha_vigencia}}</strong></p>
    </div>
    <a href="{{planes_comparativo_url}}" style="display:block;text-align:center;background:#6366F1;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      Comparar Features
    </a>
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
            "Monto: ${{monto}} CLP.\n\nGestionar suscripción: {{suscripcion_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:28px;">
    <h2 style="color:#06B6D4;margin-top:0;">🔁 Próxima renovación automática</h2>
    <p>Hola <strong>{{usuario}}</strong>,</p>
    <div style="background:#ECFEFF;border:1px solid #A5F3FC;padding:16px;border-radius:10px;margin:20px 0;">
      <p style="margin:0 0 8px 0;">📅 <strong>{{fecha_renovacion}}</strong></p>
      <p style="margin:0 0 8px 0;">Plan: <strong>{{plan}}</strong></p>
      <p style="margin:0;">🔐 Monto a cargar: <strong>${{monto}} CLP</strong></p>
    </div>
    <a href="{{suscripcion_url}}" style="display:block;text-align:center;background:#06B6D4;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;">
      Gestionar Suscripción
    </a>
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
            "Descargar PDF: {{pdf_factura_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#10B981 0%,#059669 100%);padding:32px;border-radius:14px;color:#fff;text-align:center;">
    <div style="font-size:48px;">✅</div>
    <h2 style="margin:8px 0 0 0;">¡Pago Aprobado!</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px;">
      <p style="margin:4px 0;">🧾 Factura N°: <strong>{{numero_factura}}</strong></p>
      <p style="margin:4px 0;">💲 Monto: <strong>${{monto}} CLP</strong></p>
      <p style="margin:4px 0;">📅 Fecha: <strong>{{fecha_pago}}</strong></p>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="{{pdf_factura_url}}" style="background:#4F46E5;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:600;">
        📄 Descargar Factura PDF
      </a>
    </div>
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
            "Actualiza tu medio de pago: {{metodo_pago_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#EF4444 0%,#B91C1C 100%);padding:28px;border-radius:14px;color:#fff;text-align:center;">
    <div style="font-size:40px;">⚠️</div>
    <h2 style="margin:8px 0 0 0;">Pago no procesado</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <p>Hola <strong>{{usuario}}</strong>,</p>
    <p>No pudimos procesar tu pago de <strong>${{monto}} CLP</strong>.</p>
    <div style="background:#FEF2F2;border-left:4px solid #EF4444;padding:12px 16px;border-radius:6px;">
      <p style="margin:0;"><strong>Motivo:</strong> {{motivo}}</p>
    </div>
    <a href="{{metodo_pago_url}}" style="display:block;text-align:center;background:#EF4444;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      Actualizar Medio de Pago
    </a>
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
            "Regulariza ahora: {{pagar_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:2px solid #EF4444;border-radius:14px;overflow:hidden;">
    <div style="background:#EF4444;color:#fff;padding:22px;">
      <h2 style="margin:0;">🚨 Cuenta Atrasada</h2>
    </div>
    <div style="padding:28px;">
      <p>Tu cuenta de <strong>{{negocio}}</strong> está atrasada <strong>{{dias_atraso}} días</strong>.</p>
      <div style="background:#FEF2F2;padding:16px;border-radius:10px;margin:16px 0;">
        <p style="margin:0 0 8px 0;">💲 Monto pendiente: <strong>${{monto_deuda}} CLP</strong></p>
        <p style="margin:0;">⏰ Suspensión programada: <strong>{{fecha_suspension}}</strong></p>
      </div>
      <a href="{{pagar_url}}" style="display:block;text-align:center;background:#EF4444;color:#fff;padding:14px;border-radius:10px;text-decoration:none;font-weight:600;">
        Regularizar Pago Ahora
      </a>
    </div>
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
            "Seguimiento: {{seguimiento_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:28px;">
    <h2 style="color:#6366F1;margin-top:0;">↩️ Reembolso Confirmado</h2>
    <p>Hola <strong>{{usuario}}</strong>, tu solicitud fue ingresada exitosamente.</p>
    <div style="background:#EEF2FF;padding:16px;border-radius:10px;margin:20px 0;">
      <p style="margin:4px 0;">🧾 N° Solicitud: <strong>{{numero_reembolso}}</strong></p>
      <p style="margin:4px 0;">💲 Monto: <strong>${{monto}} CLP</strong></p>
      <p style="margin:4px 0;">📅 Depósito estimado: <strong>{{fecha_estimada}}</strong></p>
    </div>
    <a href="{{seguimiento_url}}" style="display:block;text-align:center;background:#6366F1;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;">
      Ver Seguimiento
    </a>
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
            "Ver reporte completo: {{reporte_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#4F46E5,#06B6D4);padding:28px;border-radius:14px;color:#fff;">
    <h2 style="margin:0;">📊 Reporte Benchmark Semanal</h2>
    <p style="opacity:0.95;margin-top:6px;">{{negocio}} · {{rubro}} · Semana {{semana}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div style="background:#EEF2FF;padding:16px;border-radius:10px;text-align:center;">
        <div style="font-size:12px;color:#6b7280;">NPS Tú</div>
        <div style="font-size:32px;font-weight:800;color:#4F46E5;">{{nps_score}}</div>
        <div style="font-size:11px;color:#6366F1;margin-top:4px;">Rubro: {{nps_rubro}}</div>
      </div>
      <div style="background:#ECFEFF;padding:16px;border-radius:10px;text-align:center;">
        <div style="font-size:12px;color:#6b7280;">CSAT Tú</div>
        <div style="font-size:32px;font-weight:800;color:#06B6D4;">{{csat_indice}}%</div>
        <div style="font-size:11px;color:#0891B2;margin-top:4px;">Rubro: {{csat_rubro}}%</div>
      </div>
    </div>
    <p style="margin-top:20px;">Estás en el <strong>Top {{posicion_percentil}}%</strong> de {{region}}.</p>
    <a href="{{reporte_url}}" style="display:block;text-align:center;background:#4F46E5;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      Ver Reporte Completo →
    </a>
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
            "Analizar en Dashboard: {{competencia_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:24px;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="font-size:36px;">🏁</div>
      <div>
        <h3 style="margin:0;color:#4F46E5;">Actividad Competencia</h3>
        <p style="margin:0;color:#6b7280;">{{competencia}} · hace {{tiempo_minutos}} min</p>
      </div>
    </div>
    <div style="background:#f9fafb;padding:16px;border-radius:10px;margin-top:16px;">
      <div style="font-size:22px;color:#F59E0B;">
        {% for i in ''|ljust:estrellas %}⭐{% endfor %}
      </div>
      <p style="margin-top:8px;line-height:1.5;">{{texto_resena}}</p>
    </div>
    <a href="{{competencia_url}}" style="display:block;text-align:center;background:#4F46E5;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      Ver Análisis Competencia
    </a>
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
            "Ver ranking: {{ranking_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#10B981,#059669);padding:28px;border-radius:14px;color:#fff;text-align:center;">
    <div style="font-size:56px;">🚀</div>
    <h2 style="margin:8px 0 0 0;">¡Subiste {{posiciones_subidas}} puestos!</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;text-align:center;">
    <p>Hola <strong>{{usuario}}</strong>, <strong>{{negocio}}</strong> lo está haciendo genial:</p>
    <div style="background:#f0fdf4;border:2px solid #bbf7d0;padding:20px;border-radius:12px;margin:20px 0;display:inline-block;">
      <div style="font-size:14px;color:#059669;">Ahora eres el</div>
      <div style="font-size:60px;font-weight:900;color:#059669;line-height:1;">N° {{posicion_actual}}</div>
      <div style="font-size:14px;color:#059669;margin-top:4px;">de {{rubro}} en {{comuna}}</div>
    </div>
    <a href="{{ranking_url}}" style="display:inline-block;background:#10B981;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:600;">
      Ver Ranking Completo
    </a>
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
            "Generar reseñas con QR: {{qr_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#F59E0B,#D97706);color:#fff;padding:24px;border-radius:14px;">
    <h2 style="margin:0;">⚠️ Alerta Rating Competencia</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0;">
      <div style="background:#fefce8;padding:16px;border-radius:10px;border:1px solid #fde68a;text-align:center;">
        <div style="font-size:12px;color:#92400E;">TÚ</div>
        <div style="font-size:36px;font-weight:800;color:#A16207;">{{tu_rating}}⭐</div>
        <div style="font-size:12px;color:#92400E;">{{tu_cantidad}} reseñas</div>
      </div>
      <div style="background:#FEF2F2;padding:16px;border-radius:10px;border:1px solid #FECACA;text-align:center;">
        <div style="font-size:12px;color:#B91C1C;">COMPETENCIA</div>
        <div style="font-size:36px;font-weight:800;color:#DC2626;">{{competidor_rating}}⭐</div>
        <div style="font-size:12px;color:#B91C1C;">{{competidor_cantidad}} reseñas</div>
      </div>
    </div>
    <p style="text-align:center;">Diferencia actual: <strong>{{diferencia}} estrellas</strong></p>
    <a href="{{qr_url}}" style="display:block;text-align:center;background:#F59E0B;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:16px;">
      Generar + Reseñas con QR →
    </a>
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
            "Tiempo recomendado: < 1 hora.\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#EF4444;color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">🚨 NPS Detractor</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">{{local}} · hace {{tiempo}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div>
        <div style="font-size:12px;color:#6b7280;">Cliente</div>
        <div style="font-weight:700;">{{cliente_nombre}}</div>
      </div>
      <div style="text-align:center;background:#FEF2F2;border:2px solid #EF4444;padding:8px 16px;border-radius:10px;">
        <div style="font-size:28px;font-weight:900;color:#EF4444;line-height:1;">{{puntaje}}</div>
        <div style="font-size:11px;color:#991B1B;">/ 10</div>
      </div>
    </div>
    <div style="background:#FEF2F2;padding:14px;border-radius:8px;border-left:4px solid #EF4444;">
      <p style="margin:0;line-height:1.5;">💬 {{comentario}}</p>
    </div>
    <a href="{{responder_url}}" style="display:block;text-align:center;background:#EF4444;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      📨 Responder al Cliente (< 1 hora)
    </a>
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
            "Aprovecha y pide una reseña Google: {{pedir_resena_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#10B981;color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">💚 ¡Promotor NPS!</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">Oportunidad de reseña Google 👀</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div>
        <div style="font-size:12px;color:#6b7280;">Cliente</div>
        <div style="font-weight:700;">{{cliente_nombre}}</div>
      </div>
      <div style="text-align:center;background:#f0fdf4;border:2px solid #10B981;padding:8px 16px;border-radius:10px;">
        <div style="font-size:28px;font-weight:900;color:#059669;line-height:1;">{{puntaje}}</div>
        <div style="font-size:11px;color:#065F46;">/ 10 PROMOTOR</div>
      </div>
    </div>
    <div style="background:#f0fdf4;padding:14px;border-radius:8px;border-left:4px solid #10B981;">
      <p style="margin:0;line-height:1.5;">💬 {{comentario}}</p>
    </div>
    <a href="{{pedir_resena_url}}" style="display:block;text-align:center;background:#10B981;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      Pedir Reseña Google 🌟
    </a>
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
            "Ver dashboard: {{dashboard_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);padding:26px;border-radius:14px;color:#fff;">
    <h2 style="margin:0;">📈 Resumen Diario · {{fecha}}</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">{{negocio}}</p>
  </div>
  <div style="background:#fff;padding:24px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0;">
      <div style="text-align:center;background:#f9fafb;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#6b7280;">RESPUESTAS</div>
        <div style="font-size:28px;font-weight:800;color:#1f2937;">{{total_respuestas}}</div>
      </div>
      <div style="text-align:center;background:#EEF2FF;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#4F46E5;">NPS HOY</div>
        <div style="font-size:28px;font-weight:800;color:#4F46E5;">{{nps_diario}}</div>
      </div>
      <div style="text-align:center;background:#ECFEFF;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#06B6D4;">CSAT</div>
        <div style="font-size:28px;font-weight:800;color:#06B6D4;">{{csat_diario}}%</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:12px 0;">
      <div style="text-align:center;background:#f0fdf4;padding:10px;border-radius:8px;">
        <div style="font-size:11px;color:#059669;">PROMOTORES</div>
        <div style="font-weight:800;color:#059669;">{{promotores}}</div>
      </div>
      <div style="text-align:center;background:#FEF9C3;padding:10px;border-radius:8px;">
        <div style="font-size:11px;color:#A16207;">PASIVOS</div>
        <div style="font-weight:800;color:#A16207;">{{pasivos}}</div>
      </div>
      <div style="text-align:center;background:#FEF2F2;padding:10px;border-radius:8px;">
        <div style="font-size:11px;color:#B91C1C;">DETRACTORES</div>
        <div style="font-weight:800;color:#B91C1C;">{{detractores}}</div>
      </div>
    </div>
    <p>🏆 Mejor local: <strong>{{mejor_local}}</strong> (NPS {{mejor_nps}})</p>
    <a href="{{dashboard_url}}" style="display:block;text-align:center;background:#6366F1;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:16px;">
      Abrir Dashboard
    </a>
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
            "Previsualizar encuesta: {{preview_url}}\n\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#fff;border:2px solid #8B5CF6;border-radius:14px;padding:28px;">
    <h2 style="margin-top:0;color:#8B5CF6;">📝 Encuesta Custom Activada</h2>
    <p>Rubro <strong>{{rubro}}</strong> · Local <strong>{{local}}</strong></p>
    <div style="background:#f5f3ff;padding:16px;border-radius:10px;margin:16px 0;">
      <p style="margin:0;">✅ Preguntas base NPS + CSAT</p>
      <p style="margin:8px 0 0 0;">➕ <strong>{{cantidad_preguntas}}</strong> preguntas específicas rubro</p>
    </div>
    <a href="{{preview_url}}" style="display:block;text-align:center;background:#8B5CF6;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;">
      🔍 Previsualizar Encuesta
    </a>
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
            "Responder en Google (Tiempo recomendado < 24h): {{responder_g_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#F59E0B 0%,#D97706 100%);color:#fff;padding:24px;border-radius:14px 14px 0 0;">
    <h2 style="margin:0;">🌟 Nueva Reseña Google</h2>
    <p style="margin:6px 0 0 0;">{{local}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">
      <div style="width:52px;height:52px;background:#fef3c7;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#92400E;">
        {{autor|first|upper}}
      </div>
      <div style="flex:1;">
        <div style="font-weight:700;">{{autor}}</div>
        <div style="color:#F59E0B;">
          {% for s in ''|ljust:estrellas %}⭐{% endfor %}
          <span style="color:#6b7280;">{{estrellas}}.0</span>
        </div>
      </div>
    </div>
    <div style="background:#f9fafb;padding:14px;border-radius:10px;border-left:4px solid #F59E0B;">
      <p style="margin:0;line-height:1.5;">{{comentario}}</p>
    </div>
    <a href="{{responder_g_url}}" style="display:block;text-align:center;background:#F59E0B;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:20px;">
      💬 Responder en Google (< 24h)
    </a>
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
            "Responder: {{responder_g_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:#F59E0B;color:#fff;padding:22px;border-radius:14px;">
    <h2 style="margin:0;">⏰ Reseña sin responder (+48h)</h2>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="background:#FEF3C7;padding:14px;border-left:4px solid #F59E0B;border-radius:6px;margin-bottom:16px;">
      <p style="margin:0;">💡 Responder reseñas antes de 72h mejora tu <strong>SEO local Google</strong> y tu rating percibido.</p>
    </div>
    <p>De <strong>{{autor}}</strong> · {{estrellas}}⭐ en <strong>{{local}}</strong></p>
    <a href="{{responder_g_url}}" style="display:block;text-align:center;background:#F59E0B;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:16px;">
      Responder Ahora
    </a>
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
            "Sigue así: {{pedir_qr_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:600px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#10B981,#0891B2);padding:30px;border-radius:14px;color:#fff;text-align:center;">
    <div style="font-size:56px;">🎯</div>
    <h1 style="margin:10px 0 0 0;">¡Rating Meta Alcanzada!</h1>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;text-align:center;">
    <p>Hola <strong>{{usuario}}</strong>, lo lograste en <strong>{{local}}</strong>:</p>
    <div style="display:inline-block;background:#f0fdf4;border:2px solid #bbf7d0;padding:24px;border-radius:14px;margin:20px 0;">
      <div style="font-size:12px;color:#059669;">RATING ACTUAL</div>
      <div style="font-size:64px;font-weight:900;color:#059669;line-height:1;">{{rating_nuevo}}⭐</div>
      <div style="font-size:13px;color:#059669;margin-top:4px;">{{total_resenas}} reseñas totales</div>
    </div>
    <a href="{{pedir_qr_url}}" style="display:inline-block;background:#10B981;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:600;">
      Pedir Más Reseñas con QR →
    </a>
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
            "Ver todas: {{dashboard_url}}\nEquipo ClientBeat"
        ),
        "cuerpo_html": """
<div style="max-width:640px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#4F46E5 0%,#F59E0B 100%);padding:26px;border-radius:14px;color:#fff;">
    <h2 style="margin:0;">📅 Reporte Mensual Google</h2>
    <p style="margin:6px 0 0 0;opacity:0.95;">{{mes}} · {{negocio}}</p>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 14px 14px;">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0;">
      <div style="text-align:center;background:#EEF2FF;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#4F46E5;">NUEVAS</div>
        <div style="font-size:30px;font-weight:800;color:#4F46E5;">+{{cantidad_nuevas}}</div>
      </div>
      <div style="text-align:center;background:#FEF3C7;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#92400E;">RATING</div>
        <div style="font-size:30px;font-weight:800;color:#92400E;">{{rating_actual}}⭐</div>
        <div style="font-size:10px;color:#A16207;">antes {{rating_anterior}}⭐</div>
      </div>
      <div style="text-align:center;background:#f0fdf4;padding:14px;border-radius:10px;">
        <div style="font-size:11px;color:#059669;">TASA RESPUESTA</div>
        <div style="font-size:30px;font-weight:800;color:#059669;">{{tasa_respuesta}}%</div>
        <div style="font-size:10px;color:#065F46;">{{respondidas}}/{{cantidad_nuevas}}</div>
      </div>
    </div>
    <a href="{{dashboard_url}}" style="display:block;text-align:center;background:#4F46E5;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:16px;">
      Ver Reseñas en Dashboard
    </a>
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
