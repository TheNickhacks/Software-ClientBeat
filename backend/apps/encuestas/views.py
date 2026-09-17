import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.businesses.models import Local
from apps.encuestas.models import PlantillaEncuesta
from apps.encuestas.forms import RespuestaEncuestaPublicaForm, PlantillaEncuestaCustomForm


class EncuestaPublicaQRView(View):
    def _get_plantilla_for_local(self, local):
        # 1. Custom plantilla for local's negocio
        plantilla = PlantillaEncuesta.objects.filter(negocio=local.negocio, activa=True).first()
        if plantilla:
            return plantilla
        # 2. Rubro plantilla
        rubro_id = getattr(local.negocio, 'rubro_id', None)
        if rubro_id:
            plantilla = (
                PlantillaEncuesta.objects.filter(
                    activa=True,
                    rubros__id=rubro_id,
                ).order_by('orden', '-es_default').first()
            )
            if plantilla:
                return plantilla
        # 3. Default global plantilla
        return (
            PlantillaEncuesta.objects.filter(activa=True, es_default=True).first()
            or PlantillaEncuesta.objects.filter(activa=True).order_by('orden', '-es_default').first()
        )

    def get(self, request, qr_token, *args, **kwargs):
        local = get_object_or_404(Local.objects.select_related('negocio', 'comuna', 'negocio__rubro'), qr_token=qr_token, estado='ACTIVO')
        negocio = local.negocio
        plantilla = self._get_plantilla_for_local(local)
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
        plantilla = self._get_plantilla_for_local(local)
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

        try:
            from apps.notifications.services import NotificationService
            NotificationService.despachar_alerta_csat_nps(resp)
        except Exception as err_notif:
            pass

        es_excelente = (
            (resp.nps_puntaje is not None and resp.nps_puntaje >= 9) or
            (resp.csat_emocion in ['MUY_FELIZ', 'FELIZ'])
        )
        url_gracias = reverse('encuestas:encuesta_gracias', args=[qr_token])
        if es_excelente:
            url_gracias += '?rating=excelente'
        return redirect(url_gracias)


class EncuestaGraciasView(TemplateView):
    template_name = 'encuestas/gracias.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qr_token = kwargs.get('qr_token')
        ctx['rating_excelente'] = (self.request.GET.get('rating') == 'excelente')
        try:
            local = Local.objects.select_related('negocio', 'comuna').get(qr_token=qr_token)
            ctx['local'] = local
            ctx['negocio'] = local.negocio
            ctx['google_review_url'] = local.google_review_url
        except Local.DoesNotExist:
            ctx['local'] = None
            ctx['negocio'] = None
            ctx['google_review_url'] = None
        return ctx


class ConfigurarPlantillaView(LoginRequiredMixin, View):
    def get_negocio(self, request):
        user = request.user
        if hasattr(user, 'negocios') and user.negocios.exists():
            return user.negocios.first()
        if hasattr(user, 'membresias_negocios'):
            miembro = user.membresias_negocios.filter(estado='ACTIVO').select_related('negocio').first()
            if miembro:
                return miembro.negocio
        return None

    def get(self, request, *args, **kwargs):
        negocio = self.get_negocio(request)
        if not negocio:
            messages.error(request, 'No tienes un negocio asociado para configurar encuestas.')
            return redirect('pages:dashboard')

        plan = getattr(negocio, 'plan', None)
        tiene_custom = getattr(plan, 'tiene_encuestas_custom', True) if plan else True
        max_preguntas = getattr(plan, 'max_preguntas_encuesta_custom', 5) if plan else 5

        plantilla, created = PlantillaEncuesta.objects.get_or_create(
            negocio=negocio,
            defaults={
                'nombre': f'Encuesta Custom {negocio.nombre}',
                'nombre_mostrar': f'¡Tu opinión sobre {negocio.nombre} nos importa!',
                'descripcion': 'Nos ayuda a darte la mejor experiencia posible.',
                'color_primario': '#0f172a',
                'color_secundario': '#2563eb',
                'color_fondo': '#f8fafc',
            }
        )
        form = PlantillaEncuestaCustomForm(instance=plantilla)

        return render(request, 'encuestas/configurar_plantilla.html', {
            'negocio': negocio,
            'plan': plan,
            'tiene_custom': tiene_custom,
            'max_preguntas': max_preguntas,
            'plantilla': plantilla,
            'form': form,
            'preguntas_extra_json': json.dumps(plantilla.preguntas_extra or []),
        })

    def post(self, request, *args, **kwargs):
        negocio = self.get_negocio(request)
        if not negocio:
            messages.error(request, 'No tienes un negocio asociado.')
            return redirect('pages:dashboard')

        plan = getattr(negocio, 'plan', None)
        tiene_custom = getattr(plan, 'tiene_encuestas_custom', True) if plan else True
        max_preguntas = getattr(plan, 'max_preguntas_encuesta_custom', 5) if plan else 5

        if not tiene_custom:
            messages.error(request, 'Tu plan actual no incluye encuestas personalizadas. Por favor actualiza a Plan Profesional.')
            return redirect('encuestas:configurar_plantilla')

        plantilla, created = PlantillaEncuesta.objects.get_or_create(negocio=negocio)
        form = PlantillaEncuestaCustomForm(request.POST, request.FILES, instance=plantilla)

        preguntas_json_str = request.POST.get('preguntas_extra_json', '[]')
        try:
            preguntas_extra = json.loads(preguntas_json_str)
            if len(preguntas_extra) > max_preguntas:
                preguntas_extra = preguntas_extra[:max_preguntas]
        except Exception:
            preguntas_extra = plantilla.preguntas_extra

        if form.is_valid():
            inst = form.save(commit=False)
            inst.negocio = negocio
            inst.preguntas_extra = preguntas_extra
            inst.save()
            messages.success(request, '¡Plantilla de encuesta actualizada con éxito!')
            return redirect('encuestas:configurar_plantilla')

        return render(request, 'encuestas/configurar_plantilla.html', {
            'negocio': negocio,
            'plan': plan,
            'tiene_custom': tiene_custom,
            'max_preguntas': max_preguntas,
            'plantilla': plantilla,
            'form': form,
            'preguntas_extra_json': preguntas_json_str,
        })

