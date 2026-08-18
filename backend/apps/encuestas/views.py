from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from apps.businesses.models import Local
from apps.encuestas.models import PlantillaEncuesta
from apps.encuestas.forms import RespuestaEncuestaPublicaForm


class EncuestaPublicaQRView(View):
    def _get_plantilla_default(self):
        return (
            PlantillaEncuesta.objects.filter(activa=True, es_default=True).first()
            or PlantillaEncuesta.objects.filter(activa=True).order_by('orden', '-es_default').first()
        )

    def get(self, request, qr_token, *args, **kwargs):
        local = get_object_or_404(Local.objects.select_related('negocio', 'comuna', 'negocio__rubro'), qr_token=qr_token, estado='ACTIVO')
        negocio = local.negocio
        plantilla = None
        rubro_id = getattr(negocio, 'rubro_id', None)
        if rubro_id:
            plantilla = (
                PlantillaEncuesta.objects.filter(
                    activa=True,
                    rubros__id=rubro_id,
                ).order_by('orden', '-es_default').first()
            )
        if not plantilla:
            plantilla = self._get_plantilla_default()
        if not plantilla:
            messages.error(request, 'Plantilla de encuesta no configurada. Contacta al administrador.')
            return render(request, 'encuestas/qr_error.html', {'local': local}, status=404)
        form = RespuestaEncuestaPublicaForm(plantilla=plantilla)
        return render(request, 'encuestas/encuesta_publica_qr.html', {
            'local': local,
            'negocio': negocio,
            'plantilla': plantilla,
            'form': form,
            'qr_token': qr_token,
        })

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, qr_token, *args, **kwargs):
        local = get_object_or_404(Local.objects.select_related('negocio'), qr_token=qr_token, estado='ACTIVO')
        plantilla = self._get_plantilla_default()
        form = RespuestaEncuestaPublicaForm(request.POST, plantilla=plantilla)
        if not form.is_valid():
            return render(request, 'encuestas/encuesta_publica_qr.html', {
                'local': local,
                'negocio': local.negocio,
                'plantilla': plantilla,
                'form': form,
                'qr_token': qr_token,
            }, status=400)
        metadata = {
            'ua': request.META.get('HTTP_USER_AGENT', '')[:500],
            'ip': request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))[:80],
            'lang': request.META.get('HTTP_ACCEPT_LANGUAGE', '')[:100],
        }
        resp = form.save_respuesta(local=local, plantilla=plantilla, commit=False)
        resp.metadata = metadata
        resp.origen = 'QR_IMPRESO'
        resp.save()
        return redirect(reverse('encuestas:encuesta_gracias', args=[qr_token]))


class EncuestaGraciasView(TemplateView):
    template_name = 'encuestas/gracias.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qr_token = kwargs.get('qr_token')
        try:
            local = Local.objects.select_related('negocio').get(qr_token=qr_token)
            ctx['local'] = local
            ctx['negocio'] = local.negocio
        except Local.DoesNotExist:
            ctx['local'] = None
            ctx['negocio'] = None
        return ctx
