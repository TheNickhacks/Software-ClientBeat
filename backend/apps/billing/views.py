import json
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from apps.businesses.models import Negocio
from apps.billing.models import (
    Plan,
    Suscripcion,
    Pago,
    EstadoSuscripcionChoices,
    EstadoPagoChoices,
    TipoCobroChoices
)
from apps.billing.flow_service import FlowService

logger = logging.getLogger('clientbeat')


def enviar_email_evento_facturacion(suscripcion, tipo_evento: str, monto: int = 0):
    """
    Envía notificaciones transaccionales por correo electrónico con diseño corporativo para eventos de Flow:
      - 'activacion': Comprobante de activación inicial y tarjeta enrolada.
      - 'renovacion': Comprobante de pago mensual recurrente (Mes 2+).
      - 'gracia': Alerta de cobro rechazado con 3 días de gracia (Dunning).
      - 'ultima_advertencia': Último aviso de vencimiento de gracia (1 día restante).
      - 'suspension': Notificación de suspensión de cuenta por impago.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    try:
        negocio = suscripcion.negocio
        dueno = negocio.dueño
        if not dueno or not dueno.email:
            return

        domain = getattr(settings, 'SITE_DOMAIN', 'http://localhost:8000').rstrip('/')
        url_perfil = f"{domain}/accounts/perfil/"
        url_bloqueado = f"{domain}/billing/bloqueado/"
        plan_nombre = suscripcion.plan.get_nombre_mostrar() if suscripcion.plan else 'ClientBeat'
        monto_fmt = f"${int(monto):,}".replace(',', '.')
        usuario_nombre = dueno.first_name or dueno.email
        tarjeta_info = f"{suscripcion.tarjeta_tipo or 'Tarjeta'} •••• {suscripcion.tarjeta_ultimos_4 or '****'}"
        fecha_venc_str = suscripcion.fecha_vencimiento.strftime('%d/%m/%Y') if suscripcion.fecha_vencimiento else '-'

        if tipo_evento == 'activacion':
            asunto = f"✅ Suscripción Activada — {negocio.nombre} en ClientBeat"
            cuerpo = (
                f"Hola {usuario_nombre},\n\n"
                f"Tu suscripción al {plan_nombre} para '{negocio.nombre}' ha sido activada con éxito a través de Flow Chile.\n"
                f"• Medio de pago enrolado: {tarjeta_info}\n"
                f"• Monto mensual: {monto_fmt} CLP\n"
                f"• Próximo cobro automático: {fecha_venc_str}\n\n"
                f"Administra tu plan en: {url_perfil}"
            )
            ctx_html = {
                'asunto': asunto,
                'badge_texto': 'Suscripción Activa · Flow Chile',
                'titulo_header': '¡Tu plan ya está activo!',
                'subtitulo_header': f'{negocio.nombre} · {plan_nombre}',
                'usuario_nombre': usuario_nombre,
                'mensaje_principal': f"Hemos confirmado la activación de tu suscripción al {plan_nombre} para '{negocio.nombre}' y el enrolamiento seguro de tu medio de pago en Flow Chile.",
                'box_bg': '#ecfbf4',
                'box_border': '#00B879',
                'box_title_color': '#008E5C',
                'box_titulo': 'Resumen de Suscripción',
                'detalles': [
                    ('Negocio', negocio.nombre),
                    ('Plan Activo', plan_nombre),
                    ('Medio de Pago Enrolado', tarjeta_info),
                    ('Monto Mensual', f'{monto_fmt} CLP'),
                    ('Próximo Cobro Automático', fecha_venc_str),
                ],
                'nota_secundaria': 'Puedes descargar tus comprobantes de pago o administrar tus sucursales en cualquier momento desde tu panel.',
                'cta_url': url_perfil,
                'cta_texto': 'Ir a Mi Suscripción',
            }
        elif tipo_evento == 'renovacion':
            asunto = f"🧾 Comprobante de Renovación Mensual — {negocio.nombre}"
            cuerpo = (
                f"Hola {usuario_nombre},\n\n"
                f"Se ha procesado exitosamente el cobro automático mensual de tu {plan_nombre} ({monto_fmt} CLP).\n"
                f"Tu suscripción ha sido extendida por 30 días adicionales hasta el {fecha_venc_str}.\n\n"
                f"Revisa tu historial en: {url_perfil}"
            )
            ctx_html = {
                'asunto': asunto,
                'badge_texto': 'Pago Recurrente Aprobado',
                'titulo_header': 'Comprobante de Renovación Mensual',
                'subtitulo_header': f'{negocio.nombre} · {plan_nombre}',
                'usuario_nombre': usuario_nombre,
                'mensaje_principal': f"Se ha procesado exitosamente el cobro automático mensual de tu suscripción en ClientBeat. Tu cuenta ha sido renovada por 30 días adicionales.",
                'box_bg': '#eef4ff',
                'box_border': '#0B3EA6',
                'box_title_color': '#0B3EA6',
                'box_titulo': 'Detalle del Cobro',
                'detalles': [
                    ('Negocio', negocio.nombre),
                    ('Plan Renovado', plan_nombre),
                    ('Monto Pagado', f'{monto_fmt} CLP'),
                    ('Tarjeta Utilizada', tarjeta_info),
                    ('Nueva Fecha de Vencimiento', fecha_venc_str),
                ],
                'nota_secundaria': 'Puedes ver e imprimir tu comprobante tributario desde la sección Facturación en tu perfil.',
                'cta_url': url_perfil,
                'cta_texto': 'Ver Comprobante en Mi Perfil',
            }
        elif tipo_evento == 'gracia':
            dias_rest = suscripcion.dias_restantes_gracia()
            asunto = f"⚠️ Acción Requerida: Problema con tu cobro mensual en ClientBeat ({dias_rest} días de gracia)"
            cuerpo = (
                f"Hola {usuario_nombre},\n\n"
                f"No pudimos procesar el cobro automático mensual de tu {plan_nombre} para '{negocio.nombre}'.\n"
                f"Tu cuenta se mantiene activa dentro de tu período de gracia de {suscripcion.dias_gracia} días "
                f"(te quedan {dias_rest} día(s) para actualizar tu tarjeta antes de que el acceso se bloquee).\n\n"
                f"Actualiza tu tarjeta aquí: {url_perfil}"
            )
            ctx_html = {
                'asunto': asunto,
                'badge_texto': 'Período de Gracia Activo',
                'titulo_header': 'Problema con tu cobro automático',
                'subtitulo_header': f'{dias_rest} día(s) de gracia disponibles',
                'usuario_nombre': usuario_nombre,
                'mensaje_principal': f"No pudimos procesar el cargo mensual de tu {plan_nombre} para '{negocio.nombre}'. Para no interrumpir tu operación, hemos activado tu período de gracia de {suscripcion.dias_gracia} días.",
                'box_bg': '#eef4ff',
                'box_border': '#0B3EA6',
                'box_title_color': '#0B3EA6',
                'box_titulo': 'Estado de tu Suscripción',
                'detalles': [
                    ('Negocio', negocio.nombre),
                    ('Plan', plan_nombre),
                    ('Estado Actual', f'En Período de Gracia ({dias_rest} días restantes)'),
                    ('Medio de Pago con Rechazo', tarjeta_info),
                ],
                'nota_secundaria': 'Actualiza tu tarjeta de crédito o débito antes de que finalice el período de gracia para mantener el acceso continuo a tu dashboard y encuestas.',
                'cta_url': url_perfil,
                'cta_texto': 'Actualizar Medio de Pago',
            }
        elif tipo_evento == 'ultima_advertencia':
            asunto = f"🚨 Último Aviso: Mañana vence el período de gracia de {negocio.nombre} en ClientBeat"
            cuerpo = (
                f"Hola {usuario_nombre},\n\n"
                f"Este es un recordatorio urgente: te queda solo 1 día de gracia antes de que el acceso a '{negocio.nombre}' "
                f"se suspenda automáticamente por cobro mensual rechazado de tu {plan_nombre}.\n\n"
                f"Regulariza tu medio de pago hoy en: {url_perfil}"
            )
            ctx_html = {
                'asunto': asunto,
                'badge_texto': 'Último Aviso · 24 Horas Restantes',
                'titulo_header': 'Mañana vence tu período de gracia',
                'subtitulo_header': f'{negocio.nombre} · Acción Urgente',
                'usuario_nombre': usuario_nombre,
                'mensaje_principal': f"Te queda solo 1 día de gracia antes de que el acceso a '{negocio.nombre}' se suspenda automáticamente debido al cobro rechazado de tu {plan_nombre}.",
                'box_bg': '#eef4ff',
                'box_border': '#0B3EA6',
                'box_title_color': '#0B3EA6',
                'box_titulo': 'Acción Requerida Hoy',
                'detalles': [
                    ('Negocio', negocio.nombre),
                    ('Plan', plan_nombre),
                    ('Tiempo Restante', '1 día antes de suspensión'),
                ],
                'nota_secundaria': 'Regulariza tu suscripción hoy mismo con un clic para evitar la pausa de tu panel de métricas.',
                'cta_url': url_perfil,
                'cta_texto': 'Regularizar Suscripción Ahora',
            }
        elif tipo_evento == 'suspension':
            asunto = f"🔒 Cuenta Suspendida por Impago — {negocio.nombre}"
            cuerpo = (
                f"Hola {usuario_nombre},\n\n"
                f"El período de gracia de {suscripcion.dias_gracia} días ha finalizado sin poder procesar el cobro de tu {plan_nombre}.\n"
                f"El acceso al panel de '{negocio.nombre}' se encuentra temporalmente bloqueado.\n\n"
                f"Reactiva tu cuenta al instante actualizando tu medio de pago en: {url_bloqueado}"
            )
            ctx_html = {
                'asunto': asunto,
                'badge_texto': 'Suscripción Suspendida',
                'titulo_header': 'Acceso temporalmente pausado',
                'subtitulo_header': f'{negocio.nombre} · {plan_nombre}',
                'usuario_nombre': usuario_nombre,
                'mensaje_principal': f"El período de gracia de {suscripcion.dias_gracia} días ha finalizado sin poder procesar el cobro de tu {plan_nombre}. El acceso al panel de '{negocio.nombre}' se encuentra temporalmente bloqueado.",
                'box_bg': '#eef4ff',
                'box_border': '#0B3EA6',
                'box_title_color': '#0B3EA6',
                'box_titulo': 'Reactivación Inmediata',
                'detalles': [
                    ('Negocio', negocio.nombre),
                    ('Plan', plan_nombre),
                    ('Estado', 'Suspendida por Impago'),
                    ('Datos e Historial', '100% Resguardados'),
                ],
                'nota_secundaria': 'Tus encuestas, códigos QR e historial siguen 100% protegidos. Reactiva tu cuenta al instante enrolando una tarjeta válida en Flow.',
                'cta_url': url_bloqueado,
                'cta_texto': 'Reactivar Mi Cuenta en Flow',
            }
        else:
            return

        html_content = render_to_string('emails/facturacion_flow.html', ctx_html)

        send_mail(
            subject=asunto,
            message=cuerpo,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Client Beat <contactoclientbeat@gmail.com>'),
            recipient_list=[dueno.email],
            html_message=html_content,
            fail_silently=True,
        )
    except Exception as e:
        logger.warning("[Flow Email Notification] Error enviando correo (%s): %s", tipo_evento, e)


class BloqueadoView(LoginRequiredMixin, TemplateView):
    """
    Vista de bloqueo estricto (Hard Paywall) cuando la suscripción está suspendida,
    vencida fuera de gracia o pendiente de pago.
    """
    template_name = 'billing/bloqueado.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        negocio = getattr(self.request, 'negocio', None)
        if not negocio:
            negocio = self.request.user.negocios_permitidos_qs().first()

        suscripcion = None
        plan = None
        desglose = None
        cant_locales = 1

        if negocio:
            suscripcion = Suscripcion.objects.select_related('plan').filter(negocio=negocio).first()
            if suscripcion:
                plan = suscripcion.plan
            else:
                plan = Plan.get_plan_default()

            cant_locales = negocio.locales.filter(estado='ACTIVO').count() or 1
            if plan:
                desglose = plan.desglose_mensual(cant_locales)

        es_dueno = bool(
            self.request.user.is_admin_soporte or
            self.request.user.is_dueno or
            (negocio and negocio.dueño_id == self.request.user.id)
        )

        ctx.update({
            'negocio': negocio,
            'suscripcion': suscripcion,
            'plan': plan,
            'desglose': desglose,
            'cant_locales': cant_locales,
            'es_dueno': es_dueno,
            'dias_gracia': getattr(settings, 'FLOW_DIAS_GRACIA_IMPAGO', 3),
        })
        return ctx


class IniciarSuscripcionFlowView(LoginRequiredMixin, View):
    """
    Inicia el flujo de Suscripción Recurrente con Flow.
    1. Sincroniza el cliente en Flow (/customer/create)
    2. Sincroniza el plan en Flow según la cantidad de sucursales (/plans/create)
    3. Solicita la URL de registro de tarjeta Oneclick (/customer/register)
    4. Redirige al cliente a Flow para ingresar su tarjeta.
    """
    def get(self, request, *args, **kwargs):
        return self._procesar(request, request.GET)

    def post(self, request, *args, **kwargs):
        return self._procesar(request, request.POST)

    def _procesar(self, request, data):
        plan_id = data.get('plan_id')
        negocio_id = data.get('negocio_id')

        negocios = request.user.negocios_permitidos_qs()
        if negocio_id:
            negocio = get_object_or_404(negocios, id=negocio_id)
        else:
            negocio = getattr(request, 'negocio', None) or negocios.first()
            if not negocio:
                messages.error(request, 'Debes registrar un negocio antes de suscribirte.')
                return redirect('/accounts/onboarding/')

        es_dueno = bool(
            request.user.is_admin_soporte or
            request.user.is_dueno or
            negocio.dueño_id == request.user.id
        )
        if not es_dueno:
            messages.error(request, '🔒 Solo el dueño del negocio tiene autorización para configurar suscripciones y tarjetas en Flow.')
            return redirect('/accounts/perfil/')

        if plan_id:
            plan = get_object_or_404(Plan, id=plan_id, activo=True)
        else:
            suscripcion_previa = Suscripcion.objects.filter(negocio=negocio).first()
            plan = suscripcion_previa.plan if suscripcion_previa else Plan.get_plan_default()

        cant_locales = negocio.locales.filter(estado='ACTIVO').count() or 1
        monto_total = plan.calcular_monto_mensual(cant_locales)

        # 1. Obtener o crear Suscripción en BD
        suscripcion = Suscripcion.objects.filter(negocio=negocio).first()
        if not suscripcion:
            suscripcion = Suscripcion.objects.create(
                negocio=negocio,
                plan=plan,
                estado=EstadoSuscripcionChoices.PENDIENTE,
                fecha_inicio=timezone.now(),
                fecha_vencimiento=timezone.now() + timedelta(days=30),
                dias_gracia=getattr(settings, 'FLOW_DIAS_GRACIA_IMPAGO', 3),
            )
        else:
            suscripcion.plan = plan
            suscripcion.save(update_fields=['plan'])

        flow_service = FlowService()

        # 2. Sincronizar Cliente en Flow (reutilizar si ya existe en Flow)
        customer_id = suscripcion.flow_customer_id
        if customer_id and customer_id.startswith('MOCK_') and not flow_service.is_mock:
            customer_id = None

        if customer_id:
            check_cus = flow_service.obtener_cliente(customer_id)
            if check_cus.get('error') or not check_cus.get('customerId'):
                customer_id = None

        if not customer_id:
            nombre_cliente = f"{negocio.nombre} ({request.user.get_full_name() or request.user.email})"
            cliente_resp = flow_service.crear_cliente(
                nombre=nombre_cliente,
                email=request.user.email,
                external_id=f"{negocio.id}-{int(timezone.now().timestamp())}"
            )
            customer_id = cliente_resp.get('customerId')
            if not customer_id:
                logger.error("[Flow Subscription] Error creando cliente: %s", cliente_resp)
                messages.error(request, f"Error conectando con Flow: {cliente_resp.get('error', 'No se pudo crear cliente')}")
                return redirect('/accounts/perfil/')

        suscripcion.flow_customer_id = customer_id

        # 3. Sincronizar Plan Recurrente en Flow (con el monto exacto de la cuenta)
        import re
        slug_plan = re.sub(r'[^A-Za-z0-9_-]', '', plan.nombre[:15]) or 'PLAN'
        flow_plan_code = f"CB-{slug_plan}-{cant_locales}LOC-{monto_total}"
        plan_resp = flow_service.sincronizar_o_crear_plan(
            plan_id=flow_plan_code,
            nombre=f"ClientBeat {plan.get_nombre_mostrar()} ({cant_locales} sucursales)",
            monto_clp=monto_total,
            intervalo=3, # Mensual
            trial_period_days=0
        )
        suscripcion.flow_plan_id = flow_plan_code
        suscripcion.save(update_fields=['flow_customer_id', 'flow_plan_id'])

        # 4. Iniciar Enrolamiento de Tarjeta Oneclick
        domain = getattr(settings, 'SITE_DOMAIN', request.build_absolute_uri('/')[:-1]).rstrip('/')
        url_retorno = f"{domain}/billing/flow/tarjeta-retorno/"

        registro_resp = flow_service.iniciar_registro_tarjeta(
            customer_id=customer_id,
            url_retorno=url_retorno
        )

        if 'url' in registro_resp and 'token' in registro_resp:
            # Guardar token temporal en sesión para verificación al retorno
            request.session['flow_reg_token'] = registro_resp['token']
            request.session['flow_suscripcion_id'] = str(suscripcion.id)
            return redirect(registro_resp['url'])

        messages.error(request, f"Error iniciando registro de tarjeta en Flow: {registro_resp.get('error', 'Respuesta inválida')}")
        return redirect('/accounts/perfil/')


@method_decorator(csrf_exempt, name='dispatch')
class RetornoRegistroTarjetaFlowView(View):
    """
    Recibe la redirección de Flow (POST o GET) tras el enrolamiento de la tarjeta de crédito/débito.
    Valida el token, activa la suscripción recurrente en Flow y desbloquea ClientBeat.
    """
    def get(self, request, *args, **kwargs):
        return self._procesar_retorno(request)

    def post(self, request, *args, **kwargs):
        return self._procesar_retorno(request)

    def _procesar_retorno(self, request):
        token = (
            request.POST.get('token')
            or request.GET.get('token')
            or request.session.get('flow_reg_token')
        )
        if not token:
            messages.error(request, 'No se recibió el token de registro de tarjeta desde Flow.')
            return redirect('/dashboard/')

        flow_service = FlowService()
        estado_tarjeta = flow_service.obtener_estado_registro_tarjeta(token)

        suscripcion_id = request.session.get('flow_suscripcion_id')
        suscripcion = None
        if suscripcion_id:
            suscripcion = Suscripcion.objects.filter(id=suscripcion_id).first()

        # En POST cross-site desde sandbox.flow.cl la cookie de sesión SameSite=Lax puede no viajar;
        # recuperamos la suscripción mediante el customerId retornado por Flow.
        if not suscripcion and estado_tarjeta.get('customerId'):
            suscripcion = Suscripcion.objects.filter(
                flow_customer_id=estado_tarjeta.get('customerId')
            ).first()

        if not suscripcion and request.user.is_authenticated:
            negocio = getattr(request, 'negocio', None) or request.user.negocios_permitidos_qs().first()
            if negocio:
                suscripcion = Suscripcion.objects.filter(negocio=negocio).first()

        if estado_tarjeta.get('status_str') == 'REGISTRADA' or str(estado_tarjeta.get('status')) == '1':
            if suscripcion:
                # 1. Guardar tarjeta enrolada
                suscripcion.tarjeta_enrolada = True
                suscripcion.tarjeta_tipo = estado_tarjeta.get('creditCardType') or 'Tarjeta'
                suscripcion.tarjeta_ultimos_4 = str(estado_tarjeta.get('last4CardDigits') or '****')[-4:]

                # 2. Activar la Suscripción Recurrente en Flow
                sub_flow = flow_service.crear_suscripcion(
                    customer_id=suscripcion.flow_customer_id,
                    plan_id=suscripcion.flow_plan_id,
                )
                if sub_flow.get('subscriptionId'):
                    suscripcion.flow_subscription_id = sub_flow.get('subscriptionId')
                suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
                suscripcion.fecha_vencimiento = timezone.now() + timedelta(days=30)
                suscripcion.proximo_ciclo = timezone.now() + timedelta(days=30)
                suscripcion.intentos_cobro_fallidos = 0
                suscripcion.save()

                # 3. Registrar el Pago de Activación
                cant_locales = suscripcion.negocio.locales.filter(estado='ACTIVO').count() or 1
                monto = suscripcion.plan.calcular_monto_mensual(cant_locales)
                Pago.objects.create(
                    suscripcion=suscripcion,
                    flow_order_id=f"SUB-ACT-{str(suscripcion.id)[:8]}-{int(timezone.now().timestamp())}",
                    tipo_cobro=TipoCobroChoices.REGISTRO_INICIAL,
                    monto=monto,
                    estado=EstadoPagoChoices.APROBADO,
                    fecha_pago=timezone.now(),
                    firma_validada=True,
                    datos_webhook={'registro_tarjeta': estado_tarjeta, 'suscripcion_flow': sub_flow}
                )
                enviar_email_evento_facturacion(suscripcion, 'activacion', monto=monto)

            if request.user.is_authenticated:
                messages.success(request, '🎉 ¡Tu tarjeta ha sido registrada exitosamente! Tu suscripción ClientBeat está activa.')
            return redirect('/dashboard/?flow_activated=1')

        if request.user.is_authenticated:
            messages.error(request, 'El registro de tu tarjeta fue cancelado o rechazado por la pasarela.')
        return redirect('/billing/bloqueado/?flow_error=1')


class IniciarPagoFlowView(LoginRequiredMixin, View):
    """
    Ruta legacy / fallback: Redirige automáticamente al flujo de Suscripción Recurrente.
    """
    def post(self, request, *args, **kwargs):
        view = IniciarSuscripcionFlowView()
        return view.post(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class RetornoPagoFlowView(View):
    """
    Manejo de retorno transaccional simple (POST o GET desde Flow).
    """
    def get(self, request, *args, **kwargs):
        return self._procesar_retorno(request)

    def post(self, request, *args, **kwargs):
        return self._procesar_retorno(request)

    def _procesar_retorno(self, request):
        token = request.POST.get('token') or request.GET.get('token')
        if not token:
            messages.error(request, 'No se recibió token de confirmación de pago.')
            return redirect('/dashboard/')

        flow_service = FlowService()
        estado_info = flow_service.obtener_estado_pago(token)

        pago = Pago.objects.filter(datos_webhook__token=token).first()
        if not pago:
            pago = Pago.objects.filter(datos_webhook__icontains=token).first()

        if estado_info.get('status_str') == 'PAGADO':
            if pago:
                pago.estado = EstadoPagoChoices.APROBADO
                pago.fecha_pago = timezone.now()
                pago.save(update_fields=['estado', 'fecha_pago'])

                suscripcion = pago.suscripcion
                suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
                suscripcion.fecha_vencimiento = timezone.now() + timedelta(days=30)
                suscripcion.intentos_cobro_fallidos = 0
                suscripcion.save(update_fields=['estado', 'fecha_vencimiento', 'intentos_cobro_fallidos'])

            messages.success(request, '¡Tu pago ha sido procesado exitosamente! Tu plan ya está activo.')
        else:
            if pago:
                pago.estado = EstadoPagoChoices.RECHAZADO
                pago.save(update_fields=['estado'])
            messages.warning(request, 'El pago no pudo ser completado o fue cancelado.')

        return redirect('/dashboard/')


@method_decorator(csrf_exempt, name='dispatch')
class WebhookPagoFlowView(View):
    """
    Webhook central de Flow Chile (Ciclo Mes 1, Mes 2 y recurrentes).
    Escucha eventos de facturación automática:
      - invoice.paid: Cobro recurrente exitoso -> extiende 30 días la suscripción.
      - invoice.payment_failed: Cobro rechazado -> activa días de gracia o suspende la cuenta.
      - subscription.canceled: Suscripción cancelada en Flow -> revoca accesos.
    """
    def post(self, request, *args, **kwargs):
        token = request.POST.get('token')
        flow_service = FlowService()

        # 1. Caso A: Webhook con Token (Pago o Registro de Tarjeta)
        if token:
            estado_info = flow_service.obtener_estado_pago(token)
            pago = Pago.objects.filter(datos_webhook__token=token).first()
            if not pago:
                pago = Pago.objects.filter(datos_webhook__icontains=token).first()

            if pago and estado_info.get('status_str') == 'PAGADO':
                pago.estado = EstadoPagoChoices.APROBADO
                pago.fecha_pago = timezone.now()
                pago.datos_webhook.update(estado_info)
                pago.save()

                suscripcion = pago.suscripcion
                suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
                suscripcion.fecha_vencimiento = timezone.now() + timedelta(days=30)
                suscripcion.proximo_ciclo = timezone.now() + timedelta(days=30)
                suscripcion.intentos_cobro_fallidos = 0
                suscripcion.save()

                return JsonResponse({'status': 'ok', 'message': 'Pago confirmado correctamente'})

        # 2. Caso B: Evento JSON de Suscripciones (Mes 2 en adelante / Invoices automáticos)
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            payload = request.POST.dict()

        header_sig = request.headers.get('X-Flow-Signature') or request.META.get('HTTP_X_FLOW_SIGNATURE')
        firma_ok = flow_service.validar_firma_webhook(payload, header_signature=header_sig, raw_body=request.body)
        if not firma_ok:
            logger.error("[Flow Webhook] Firma criptográfica inválida rechazada: %s", payload)
            return JsonResponse({'status': 'error', 'message': 'Firma criptográfica inválida'}, status=403)

        evento = payload.get('event') or payload.get('type')
        subscription_id = payload.get('subscriptionId') or payload.get('subscription_id')
        customer_id = payload.get('customerId') or payload.get('customer_id')

        suscripcion = None
        if subscription_id:
            suscripcion = Suscripcion.objects.filter(flow_subscription_id=subscription_id).first()
        if not suscripcion and customer_id:
            suscripcion = Suscripcion.objects.filter(flow_customer_id=customer_id).first()

        if not suscripcion:
            logger.warning("[Flow Webhook] Suscripción no encontrada para evento %s: %s", evento, payload)
            return JsonResponse({'status': 'ignored', 'message': 'Suscripción no encontrada'})

        # Manejo de eventos del ciclo mensual
        if evento in ['invoice.paid', 'payment.paid']:
            # Cobro exitoso del nuevo mes
            suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
            suscripcion.fecha_vencimiento = timezone.now() + timedelta(days=30)
            suscripcion.proximo_ciclo = timezone.now() + timedelta(days=30)
            suscripcion.intentos_cobro_fallidos = 0
            suscripcion.save()

            monto = int(payload.get('amount') or suscripcion.plan.precio_clp or 0)
            Pago.objects.create(
                suscripcion=suscripcion,
                flow_order_id=payload.get('invoiceId') or f"REC-{int(timezone.now().timestamp())}",
                flow_invoice_id=payload.get('invoiceId'),
                tipo_cobro=TipoCobroChoices.CICLO_RECURRENTE,
                monto=monto,
                estado=EstadoPagoChoices.APROBADO,
                fecha_pago=timezone.now(),
                firma_validada=firma_ok,
                datos_webhook=payload
            )
            enviar_email_evento_facturacion(suscripcion, 'renovacion', monto=monto)
            logger.info("[Flow Webhook] Renovación automática exitosa para suscripción %s", suscripcion.id)
            return JsonResponse({'status': 'ok', 'message': 'Renovación procesada'})

        elif evento in ['invoice.payment_failed', 'invoice.overdue']:
            # Fallo en el débito automático del segundo mes
            suscripcion.intentos_cobro_fallidos += 1
            suscripcion.fecha_ultimo_intento_cobro = timezone.now()

            # Evaluar días de gracia (3 días)
            dias_gracia = suscripcion.dias_gracia or getattr(settings, 'FLOW_DIAS_GRACIA_IMPAGO', 3)
            limite_gracia = suscripcion.fecha_vencimiento + timedelta(days=dias_gracia)
            if dias_gracia > 0 and timezone.now() <= limite_gracia:
                suscripcion.estado = EstadoSuscripcionChoices.EN_GRACIA
                tipo_alerta = 'gracia'
            else:
                suscripcion.estado = EstadoSuscripcionChoices.SUSPENDIDA
                tipo_alerta = 'suspension'

            suscripcion.save()
            enviar_email_evento_facturacion(suscripcion, tipo_alerta)
            logger.warning("[Flow Webhook] Fallo de cobro registrado para suscripción %s. Estado: %s", suscripcion.id, suscripcion.estado)
            return JsonResponse({'status': 'ok', 'message': f'Cobro fallido registrado. Estado: {suscripcion.estado}'})

        elif evento in ['subscription.canceled']:
            suscripcion.estado = EstadoSuscripcionChoices.CANCELADA
            suscripcion.cancelada_en = timezone.now()
            suscripcion.save()
            return JsonResponse({'status': 'ok', 'message': 'Suscripción cancelada'})

        return JsonResponse({'status': 'ignored', 'message': 'Evento no manejado'})


class ComprobantePagoView(LoginRequiredMixin, TemplateView):
    """
    Vista de comprobante tributario / recibo imprimible (PDF vía navegador) para cualquier
    pago procesado en ClientBeat.
    """
    template_name = 'billing/comprobante_pago.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pago_id = self.kwargs.get('pago_id')
        pago = get_object_or_404(
            Pago.objects.select_related('suscripcion', 'suscripcion__negocio', 'suscripcion__plan'),
            id=pago_id
        )
        negocio = pago.suscripcion.negocio
        # Verificar permisos: dueño del negocio, miembro del equipo o admin soporte
        if not (
            self.request.user.is_admin_soporte or
            self.request.user.is_superuser or
            negocio.id in self.request.user.negocios_permitidos_qs().values_list('id', flat=True)
        ):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para ver este comprobante.")

        monto_neto = pago.monto
        monto_iva = int(round(monto_neto * 0.19))
        monto_total_con_iva = monto_neto + monto_iva

        ctx.update({
            'pago': pago,
            'suscripcion': pago.suscripcion,
            'negocio': negocio,
            'plan': pago.suscripcion.plan,
            'monto_neto': monto_neto,
            'monto_iva': monto_iva,
            'monto_total_con_iva': monto_total_con_iva,
            'empresa': getattr(settings, 'EMPRESA', {
                'NOMBRE': 'Client Beat SpA',
                'RUT': '77.607.311-3',
                'DOMICILIO': 'Asturias 790 E, Rancagua',
                'CONTACTO': 'contactoclientbeat@gmail.com',
                'SITIO_WEB': 'www.clientbeat.cl',
            }),
        })
        return ctx
