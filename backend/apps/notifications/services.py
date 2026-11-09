import logging
from typing import Optional, Dict, Any
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context

from apps.notifications.models import Notificacion, PlantillaNotificacion, CategoriaNotificacionChoices

logger = logging.getLogger('clientbeat')


class NotificationService:
    """
    Motor centralizado de generación y despacho de alertas y notificaciones en tiempo real
    vía In-App y Email.
    """

    @classmethod
    def enviar_notificacion(
        cls,
        usuario,
        negocio,
        codigo_plantilla: str,
        context_data: Dict[str, Any],
        canal: str = 'IN_APP',
        fallback_titulo: str = "Alerta ClientBeat",
        fallback_mensaje: str = "Tienes una nueva notificación.",
    ) -> Optional[Notificacion]:
        """
        Busca la plantilla por codigo_unico, renderiza las variables de contexto
        y guarda la notificación In-App y envía email si corresponde.
        """
        plantilla = PlantillaNotificacion.objects.filter(codigo_unico=codigo_plantilla, activo=True).first()

        if plantilla:
            try:
                t_asunto = Template(plantilla.asunto_email)
                t_html = Template(plantilla.cuerpo_html)
                ctx = Context(context_data)

                asunto_final = t_asunto.render(ctx)
                cuerpo_final = t_html.render(ctx)
                mensaje_plano = plantilla.cuerpo_texto_plano or cuerpo_final
            except Exception as e:
                logger.error("[NotificationService] Error renderizando plantilla %s: %s", codigo_plantilla, e)
                asunto_final = fallback_titulo
                cuerpo_final = fallback_mensaje
                mensaje_plano = fallback_mensaje
        else:
            from django.template.loader import render_to_string
            asunto_final = fallback_titulo
            mensaje_plano = fallback_mensaje
            domain = getattr(settings, 'SITE_DOMAIN', 'http://localhost:8000').rstrip('/')
            cuerpo_final = render_to_string('emails/facturacion_flow.html', {
                'asunto': asunto_final,
                'badge_texto': 'Notificación ClientBeat',
                'titulo_header': fallback_titulo,
                'subtitulo_header': getattr(negocio, 'nombre', 'ClientBeat'),
                'usuario_nombre': getattr(usuario, 'first_name', None) or getattr(usuario, 'email', 'Cliente'),
                'mensaje_principal': fallback_mensaje,
                'box_bg': '#eef4ff',
                'box_border': '#0B3EA6',
                'box_title_color': '#0B3EA6',
                'box_titulo': 'Resumen de Alerta',
                'detalles': [('Negocio', getattr(negocio, 'nombre', 'ClientBeat'))],
                'nota_secundaria': 'Ingresa a tu panel para gestionar esta notificación.',
                'cta_url': f'{domain}/dashboard/',
                'cta_texto': 'Ir al Dashboard',
            })

        # 1. Guardar notificación In-App
        notif = Notificacion.objects.create(
            usuario=usuario,
            negocio=negocio,
            titulo=asunto_final,
            mensaje=cuerpo_final,
            tipo='ALERTA',
            canal=canal,
            leida=False,
        )

        # 2. Despachar Email si hay dirección de usuario
        email_destinatario = getattr(usuario, 'email', None) or getattr(negocio, 'email_contacto', None)
        if email_destinatario and canal in ['EMAIL', 'AMBOS']:
            try:
                send_mail(
                    subject=asunto_final,
                    message=mensaje_plano,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Client Beat <contactoclientbeat@gmail.com>'),
                    recipient_list=[email_destinatario],
                    html_message=cuerpo_final,
                    fail_silently=True,
                )
                logger.info("[NotificationService] Email enviado exitosamente a %s", email_destinatario)
            except Exception as e:
                logger.error("[NotificationService] Error enviando email a %s: %s", email_destinatario, e)

        return notif

    @classmethod
    def despachar_alerta_csat_nps(cls, respuesta) -> Optional[Notificacion]:
        """
        Alerta si una encuesta tiene un Detractor (NPS <= 6) o Insatisfacción en CSAT.
        """
        if not respuesta or not respuesta.local:
            return None

        negocio = respuesta.local.negocio
        dueño = negocio.dueño if negocio else None

        nps = respuesta.nps_puntaje
        csat = respuesta.csat_emocion

        es_detractor = (nps is not None and nps <= 6)
        es_insatisfecho = csat in ['INSATISFECHO', 'MUY_INSATISFECHO']

        if not (es_detractor or es_insatisfecho):
            return None

        domain = getattr(settings, 'SITE_DOMAIN', 'http://localhost:8000').rstrip('/')
        contexto = {
            'usuario': (dueño.first_name or dueño.email) if dueño else 'Equipo',
            'negocio': negocio.nombre if negocio else 'Tu negocio',
            'local': respuesta.local.nombre,
            'cliente_nombre': getattr(respuesta, 'cliente_nombre', None) or 'Cliente en sucursal',
            'puntaje': nps if nps is not None else 'N/A',
            'nps': nps if nps is not None else 'N/A',
            'csat': respuesta.get_csat_emocion_display() if csat else 'N/A',
            'comentario': respuesta.comentario or 'Sin comentario adicional',
            'tiempo': 'unos instantes',
            'responder_url': f'{domain}/dashboard/',
        }

        titulo = f"⚠️ Alerta de Calificación Baja en {respuesta.local.nombre}"
        mensaje = f"Se ha registrado una calificación baja (NPS {nps}/10). Comentario: '{respuesta.comentario or 'Sin comentario'}'."

        return cls.enviar_notificacion(
            usuario=dueño,
            negocio=negocio,
            codigo_plantilla='NPS-001-DETRACTOR-ALERTA',
            context_data=contexto,
            canal='AMBOS',
            fallback_titulo=titulo,
            fallback_mensaje=mensaje,
        )

    @classmethod
    def despachar_alerta_resena_negativa(cls, resena) -> Optional[Notificacion]:
        """
        Alerta inmediata ante una reseña negativa de 1 o 2 estrellas en Google.
        """
        if not resena or not resena.local:
            return None

        negocio = resena.local.negocio
        dueño = negocio.dueño if negocio else None

        if resena.calificacion > 2:
            return None

        domain = getattr(settings, 'SITE_DOMAIN', 'http://localhost:8000').rstrip('/')
        contexto = {
            'usuario': (dueño.first_name or dueño.email) if dueño else 'Equipo',
            'negocio': negocio.nombre if negocio else 'Tu negocio',
            'local': resena.local.nombre,
            'calificacion': resena.calificacion,
            'estrellas': resena.calificacion,
            'autor': resena.autor_nombre,
            'comentario': resena.comentario or 'Sin texto',
            'responder_g_url': f'{domain}/dashboard/resenas/',
        }

        titulo = f"🚨 Reseña de {resena.calificacion}★ recibida en Google Maps ({resena.local.nombre})"
        mensaje = f"{resena.autor_nombre} publicó una reseña de {resena.calificacion} estrellas: '{resena.comentario or 'Sin texto'}'."

        return cls.enviar_notificacion(
            usuario=dueño,
            negocio=negocio,
            codigo_plantilla='G-RESEÑA-001-NUEVA-CALIFICADA',
            context_data=contexto,
            canal='AMBOS',
            fallback_titulo=titulo,
            fallback_mensaje=mensaje,
        )
