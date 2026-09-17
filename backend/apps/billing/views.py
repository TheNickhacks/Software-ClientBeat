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

from apps.businesses.models import Negocio
from apps.billing.models import Plan, Suscripcion, Pago, EstadoSuscripcionChoices, EstadoPagoChoices
from apps.billing.flow_service import FlowService

logger = logging.getLogger('clientbeat')


class IniciarPagoFlowView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        plan_id = request.POST.get('plan_id')
        negocio_id = request.POST.get('negocio_id')

        plan = get_object_or_404(Plan, id=plan_id, activo=True)
        if negocio_id:
            negocio = get_object_or_404(Negocio, id=negocio_id, dueño=request.user)
        else:
            negocio = request.user.negocios.first()
            if not negocio:
                messages.error(request, 'Debes registrar un negocio antes de realizar un pago.')
                return redirect('accounts:onboarding')

        cant_locales = negocio.locales.count() or 1
        monto_total = plan.calcular_monto_mensual(cant_locales)

        suscripcion = Suscripcion.objects.filter(negocio=negocio).first()
        if not suscripcion:
            suscripcion = Suscripcion.objects.create(
                negocio=negocio,
                plan=plan,
                estado=EstadoSuscripcionChoices.PENDIENTE,
                fecha_inicio=timezone.now(),
                fecha_vencimiento=timezone.now() + timedelta(days=30),
            )
        else:
            suscripcion.plan = plan
            suscripcion.save(update_fields=['plan'])

        flow_service = FlowService()
        orden_compra = f"CB-{str(suscripcion.id)[:8]}-{int(timezone.now().timestamp())}"

        domain = request.build_absolute_uri('/')[:-1]
        url_retorno = f"{domain}/billing/flow/retorno/"
        url_confirmacion = f"{domain}/billing/flow/webhook/"

        resultado = flow_service.crear_orden_pago(
            orden_compra=orden_compra,
            monto=monto_total,
            concepto=f"Suscripción Plan {plan.get_nombre_mostrar()} - {negocio.nombre}",
            email_pagador=request.user.email,
            url_retorno=url_retorno,
            url_confirmacion=url_confirmacion,
        )

        if 'error' in resultado:
            messages.error(request, f"Error iniciando pago con Flow: {resultado['error']}")
            return redirect('billing:planes')

        Pago.objects.create(
            suscripcion=suscripcion,
            flow_order_id=str(resultado.get('flowOrder') or orden_compra),
            monto=monto_total,
            estado=EstadoPagoChoices.PENDIENTE,
            datos_webhook={'url': resultado['url'], 'token': resultado['token'], 'is_mock': resultado.get('is_mock', False)},
        )

        return redirect(resultado['url'])


class RetornoPagoFlowView(View):
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
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
                suscripcion.save(update_fields=['estado', 'fecha_vencimiento'])

            messages.success(request, '¡Tu pago ha sido procesado exitosamente! Tu plan ya está activo.')
        else:
            if pago:
                pago.estado = EstadoPagoChoices.RECHAZADO
                pago.save(update_fields=['estado'])
            messages.warning(request, 'El pago no pudo ser completado o fue cancelado.')

        return redirect('/dashboard/')


@method_decorator(csrf_exempt, name='dispatch')
class WebhookPagoFlowView(View):
    def post(self, request, *args, **kwargs):
        token = request.POST.get('token')
        if not token:
            return JsonResponse({'status': 'error', 'message': 'Missing token'}, status=400)

        flow_service = FlowService()
        estado_info = flow_service.obtener_estado_pago(token)

        pago = Pago.objects.filter(datos_webhook__token=token).first()
        if pago and estado_info.get('status_str') == 'PAGADO':
            pago.estado = EstadoPagoChoices.APROBADO
            pago.fecha_pago = timezone.now()
            pago.datos_webhook.update(estado_info)
            pago.save()

            suscripcion = pago.suscripcion
            suscripcion.estado = EstadoSuscripcionChoices.ACTIVA
            suscripcion.fecha_vencimiento = timezone.now() + timedelta(days=30)
            suscripcion.save()

            return JsonResponse({'status': 'ok', 'message': 'Pago confirmado correctamente'})

        return JsonResponse({'status': 'ignored', 'message': 'Token no procesado'})
