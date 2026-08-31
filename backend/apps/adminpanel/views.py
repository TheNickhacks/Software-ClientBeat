from django.views.generic import TemplateView, ListView, CreateView, UpdateView, View, DetailView
from django.db import connection, transaction
from django.db.models import Count, Sum, Avg, Q, IntegerField, F, ExpressionWrapper, Case, When, Value
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from .mixins import AdminSoporteRequiredMixin, SuperUserRequiredMixin
from .forms import PlanForm
from .models import (
    AuditoriaAdmin,
    AccionAuditoriaChoices,
    ModuloAuditoriaChoices,
    ConfiguracionMetricas,
)

from apps.billing.models import (
    Plan,
    Suscripcion,
    Pago,
    EstadoSuscripcionChoices,
    EstadoPagoChoices,
    CambioPlan,
    MotivoCambioPlanChoices,
)
from apps.encuestas.models import PlantillaEncuesta
from apps.geo.models import Rubro
from apps.businesses.models import Negocio, Local, MiembroEquipo
RolChoices = MiembroEquipo.RolChoices


User = get_user_model()


def _auditar(request, accion, modulo, entidad, *, descripcion=None, datos_antes=None, datos_despues=None, notas=None):
    """Helper corto para registrar auditoría desde cualquier vista."""
    try:
        return AuditoriaAdmin.registrar(
            request=request,
            accion=accion,
            modulo=modulo,
            entidad=entidad,
            descripcion=descripcion,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            notas=notas,
        )
    except Exception:
        return None


def _estado_sus_color(e):
    return {
        EstadoSuscripcionChoices.ACTIVA: 'emerald',
        EstadoSuscripcionChoices.PENDIENTE: 'amber',
        EstadoSuscripcionChoices.VENCIDA: 'rose',
        EstadoSuscripcionChoices.SUSPENDIDA: 'orange',
        EstadoSuscripcionChoices.CANCELADA: 'slate',
    }.get(e, 'slate')


def _estado_pago_color(e):
    return {
        EstadoPagoChoices.APROBADO: 'emerald',
        EstadoPagoChoices.PENDIENTE: 'amber',
        EstadoPagoChoices.RECHAZADO: 'rose',
        EstadoPagoChoices.REEMBOLSADO: 'slate',
    }.get(e, 'slate')


def modulos_menu(request):
    """Menú jerárquico unificado de administración de servicios."""
    return [
        {
            'section': 'Reportería',
            'key': 'reporteria',
            'icono': 'fa-chart-pie',
            'submodulos': [
                {'label': '1.1 Listado de clientes', 'url': reverse_lazy('adminpanel:reporteria_clientes'), 'icono': 'fa-users', 'key': 'reporteria_clientes'},
                {'label': '1.2 Benchmark por rubro', 'url': reverse_lazy('adminpanel:reporteria_benchmark_rubro'), 'icono': 'fa-chart-line', 'key': 'reporteria_benchmark_rubro'},
                {'label': '1.3 Tendencias en reseñas', 'url': reverse_lazy('adminpanel:reporteria_tendencias_resenas'), 'icono': 'fa-comments', 'key': 'reporteria_tendencias_resenas'},
                {'label': '1.4 Reportes de Planes', 'url': reverse_lazy('adminpanel:reporteria_planes'), 'icono': 'fa-tags', 'key': 'reporteria_planes'},
            ]
        },
        {
            'section': 'Data Google',
            'key': 'data_google',
            'icono': 'fa-database',
            'submodulos': [
                {'label': '2.1 Rubros y Preguntas', 'url': reverse_lazy('adminpanel:datagoogle_rubros'), 'icono': 'fa-layer-group', 'key': 'datagoogle_rubros'},
            ]
        },
        {
            'section': 'Métricas',
            'key': 'metricas',
            'icono': 'fa-sliders-h',
            'submodulos': [
                {'label': '3.1 Criterios de Benchmark', 'url': reverse_lazy('adminpanel:metricas_criterios_benchmark'), 'icono': 'fa-balance-scale', 'key': 'metricas_criterios_benchmark'},
                {'label': '3.2 CSAT y NPS', 'url': reverse_lazy('adminpanel:metricas_csat_nps'), 'icono': 'fa-smile', 'key': 'metricas_csat_nps'},
                {'label': '3.3 Reseñas Google', 'url': reverse_lazy('adminpanel:metricas_resenas_google'), 'icono': 'fa-star', 'key': 'metricas_resenas_google'},
            ]
        },
        {
            'section': 'Planes',
            'key': 'planes',
            'icono': 'fa-cubes',
            'submodulos': [
                {'label': '4.1 Editar Planes', 'url': reverse_lazy('adminpanel:planes_editar'), 'icono': 'fa-edit', 'key': 'planes_editar'},
            ]
        },
        {
            'section': 'Recursos',
            'key': 'recursos',
            'icono': 'fa-award',
            'submodulos': [
                {'label': '5.1 Programa de Reconocimiento', 'url': reverse_lazy('adminpanel:recursos_reconocimiento'), 'icono': 'fa-award', 'key': 'recursos_reconocimiento'},
            ]
        },
        {
            'section': 'Notificaciones',
            'key': 'notificaciones',
            'icono': 'fa-bell',
            'submodulos': [
                {'label': '6.1 Editar y Emitir', 'url': reverse_lazy('adminpanel:notificaciones'), 'icono': 'fa-paper-plane', 'key': 'notificaciones'},
            ]
        },
    ]



# ==============================
# DASHBOARD PRINCIPAL
# ==============================
class AdminPanelDashboardView(AdminSoporteRequiredMixin, TemplateView):
    """Dashboard principal KPI Admin Soporte no-técnico."""
    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ahora = timezone.now()
        desde_30d = ahora - timezone.timedelta(days=30)
        desde_7d = ahora - timezone.timedelta(days=7)

        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Dashboard'

        # 1) KPIs principales
        negocios_activos = Negocio.objects.filter(estado='ACTIVO').count()
        neg_nuevos_7d = Negocio.objects.filter(fecha_creacion__gte=desde_7d).count()
        suscripciones_activas = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.ACTIVA).count()
        sus_pendientes = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.PENDIENTE).count()
        sus_canceladas_30d = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.CANCELADA, cancelada_en__gte=desde_30d).count()
        usuarios_activos = User.objects.filter(is_active=True).count()
        planes_activos = Plan.objects.filter(activo=True).count()
        locales_total = Local.objects.count()
        respuestas_30d = 0
        try:
            from apps.encuestas.models import RespuestaEncuesta
            respuestas_30d = RespuestaEncuesta.objects.filter(fecha_respuesta__gte=desde_30d).count()
        except Exception:
            pass
        rubros_activos = Rubro.objects.filter(activo=True).count()
        # Vencen 7 días
        vencen_7d = Suscripcion.objects.filter(
            estado=EstadoSuscripcionChoices.ACTIVA,
            fecha_vencimiento__lte=ahora + timezone.timedelta(days=7),
            fecha_vencimiento__gte=ahora,
        ).count()
        # Pagos pendientes
        pagos_pendientes = Pago.objects.filter(estado=EstadoPagoChoices.PENDIENTE).count()
        # Auditorías 7 días
        audits_7d = AuditoriaAdmin.objects.filter(fecha_hora__gte=desde_7d).count()
        # Cambios de plan 30 días
        cambios_plan = CambioPlan.objects.filter(fecha_cambio__gte=desde_30d).count()
        # Benchmark / Reputación KPIs
        google_total = 0
        benchmark_7d = 0
        locales_gpid_pct = 0
        locales_con_gpid = 0
        try:
            from apps.reputation.models import ResenaGoogle, Benchmark
            google_total = ResenaGoogle.objects.count()
            benchmark_7d = Benchmark.objects.filter(fecha_generacion__gte=desde_7d).count()
            locales_con_gpid = Local.objects.exclude(google_place_id__isnull=True).exclude(google_place_id='').count()
            locales_gpid_pct = int(round(100.0 * locales_con_gpid / max(1, locales_total))) if locales_total else 0
        except Exception:
            pass

        ctx['kpis'] = [
            ('Negocios activos', negocios_activos, 'text-fuchsia-700', 'bg-fuchsia-100', 'fa-store', f'+{neg_nuevos_7d} esta semana' if neg_nuevos_7d else ''),
            ('Suscripciones activas', suscripciones_activas, 'text-emerald-700', 'bg-emerald-100', 'fa-credit-card', f'{sus_pendientes} pendientes' if sus_pendientes else ''),
            ('Cancelaciones 30d', sus_canceladas_30d, 'text-rose-700', 'bg-rose-100', 'fa-user-minus', ''),
            ('Vencen ≤ 7 días', vencen_7d, 'text-amber-700', 'bg-amber-100', 'fa-bell', ''),
            ('Usuarios plataforma', usuarios_activos, 'text-blue-700', 'bg-blue-100', 'fa-users', ''),
            ('Planes disponibles', planes_activos, 'text-indigo-700', 'bg-indigo-100', 'fa-tags', ''),
            ('Locales totales', locales_total, 'text-purple-700', 'bg-purple-100', 'fa-location-dot', ''),
            ('Respuestas 30d', respuestas_30d, 'text-sky-700', 'bg-sky-100', 'fa-comments', ''),
            ('Cambios de Plan 30d', cambios_plan, 'text-violet-700', 'bg-violet-100', 'fa-exchange-alt', ''),
            ('Pagos pendientes', pagos_pendientes, 'text-orange-700', 'bg-orange-100', 'fa-hourglass-half', ''),
            ('Auditorías 7d', audits_7d, 'text-slate-700', 'bg-slate-100', 'fa-clipboard-check', ''),
            ('Rubros activos', rubros_activos, 'text-teal-700', 'bg-teal-100', 'fa-list-check', ''),
            ('Reseñas Google', google_total, 'text-yellow-700', 'bg-yellow-100', 'fa-star', ''),
            ('Benchmarks 7d', benchmark_7d, 'text-lime-700', 'bg-lime-100', 'fa-trophy', ''),
            ('Locales c/ Google ID', locales_gpid_pct, 'text-cyan-700', 'bg-cyan-100', 'fa-map-location-dot', '%s/%s' % (locales_con_gpid, locales_total) if locales_total else ''),
        ]

        # 2) Rubros Top
        rubros_top = list(
            Rubro.objects.filter(activo=True)
            .annotate(total_negocios=Count('negocios', distinct=True))
            .order_by('-total_negocios')[:8]
        )
        rubros_top_max = max((r.total_negocios for r in rubros_top), default=1)
        ctx['rubros_top'] = [
            {
                'nombre': r.nombre,
                'total_negocios': r.total_negocios,
                'pct': round(100 * r.total_negocios / rubros_top_max) if rubros_top_max else 0,
            }
            for r in rubros_top
        ]

        # 3) Ventas por Plan
        ventas_planes = list(
            Suscripcion.objects
            .filter(estado=EstadoSuscripcionChoices.ACTIVA)
            .values('plan__id', 'plan__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        planes_ids = [vp['plan__id'] for vp in ventas_planes if vp.get('plan__id')]
        planes_by_id = {p.id: p for p in Plan.objects.filter(id__in=planes_ids)} if planes_ids else {}
        ventas_planes_list = []
        for vp in ventas_planes:
            plan = planes_by_id.get(vp['plan__id'])
            nombre = plan.get_nombre_mostrar() if plan else (vp['plan__nombre'] or 'MVP Básico')
            color = 'bg-slate-500'
            ventas_planes_list.append({'nombre': nombre, 'total': vp['total'], 'color': color})
        ctx['ventas_planes'] = ventas_planes_list
        ctx['ventas_planes_total'] = sum(v['total'] for v in ventas_planes_list) or 1

        # 4) Roles distribución
        roles_dist = []
        for rol_key, rol_label in RolChoices.choices:
            cnt = MiembroEquipo.objects.filter(rol=rol_key, estado='ACTIVO').count()
            roles_dist.append({'label': rol_label, 'key': rol_key, 'total': cnt})
        roles_total = sum(r['total'] for r in roles_dist) or 1
        for r in roles_dist:
            r['pct'] = round(100 * r['total'] / roles_total)
        ctx['roles_distribucion'] = sorted(roles_dist, key=lambda x: -x['total'])

        # 5) NPS plataforma últimos 30d
        try:
            from apps.encuestas.models import RespuestaEncuesta
            resp_30d_nps = RespuestaEncuesta.objects.filter(
                fecha_respuesta__gte=desde_30d, nps_puntaje__isnull=False
            )
            total_nps = resp_30d_nps.count()
            if total_nps:
                promotores = resp_30d_nps.filter(nps_puntaje__gte=9).count()
                pasivos = resp_30d_nps.filter(nps_puntaje__in=[7, 8]).count()
                detractores = resp_30d_nps.filter(nps_puntaje__lte=6).count()
                score = round(100 * (promotores - detractores) / total_nps)
                prom = resp_30d_nps.aggregate(prom=Avg('nps_puntaje'))['prom'] or 0
            else:
                promotores = pasivos = detractores = score = prom = total_nps = 0
        except Exception:
            promotores = pasivos = detractores = score = prom = total_nps = 0
        ctx['nps_plataforma'] = {
            'score': score, 'promedio': round(prom, 1), 'total': total_nps,
            'promotores': promotores, 'pasivos': pasivos, 'detractores': detractores,
            'badge': 'Promotor' if score >= 50 else 'Pasivo' if score >= 0 else 'Detractor',
            'color': 'emerald' if score >= 50 else 'amber' if score >= 0 else 'rose',
        }

        # 6) Últimos negocios, auditorías, suscripciones a vencer
        ctx['ultimos_negocios'] = (
            Negocio.objects.select_related('dueño', 'comuna')
            .annotate(cant_locales=Count('locales'))
            .order_by('-fecha_creacion')[:6]
        )
        ctx['vencen_7dias'] = (
            Suscripcion.objects.select_related('negocio', 'plan')
            .filter(estado=EstadoSuscripcionChoices.ACTIVA)
            .order_by('fecha_vencimiento')[:6]
        )
        ctx['auditoria_reciente'] = (
            AuditoriaAdmin.objects.select_related('usuario')
            .order_by('-fecha_hora')[:10]
        )
        ctx['cambios_plan_reciente'] = (
            CambioPlan.objects.select_related('plan_anterior', 'plan_nuevo', 'suscripcion', 'suscripcion__negocio', 'realizado_por')
            .order_by('-fecha_cambio')[:6]
        )
        ctx['suscripciones_pendientes'] = (
            Suscripcion.objects.select_related('negocio', 'plan')
            .filter(estado=EstadoSuscripcionChoices.PENDIENTE)
            .order_by('-fecha_inicio')[:6]
        )
        ctx['planes'] = Plan.objects.filter(activo=True).order_by('orden')
        ctx['fecha_hora_generacion'] = timezone.localtime(ahora).strftime('%Y-%m-%d %H:%M:%S')
        ctx['_estado_sus_color'] = _estado_sus_color
        return ctx


# ==============================
# MÓDULO 1: SUSCRIPCIONES
# ==============================
class AdminPanelSuscripcionesListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/suscripciones_list.html'
    model = Suscripcion
    context_object_name = 'suscripciones'
    paginate_by = 20

    def get_queryset(self):
        qs = Suscripcion.objects.select_related('negocio', 'negocio__dueño', 'plan').prefetch_related('pagos').all()
        filtros = {}
        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '').strip()
        plan_id = self.request.GET.get('plan', '').strip()
        renovacion = self.request.GET.get('renovacion', '').strip()
        if q:
            qs = qs.filter(
                Q(negocio__nombre__icontains=q)
                | Q(negocio__rut__icontains=q)
                | Q(negocio__dueño__email__icontains=q)
                | Q(id__icontains=q)
            )
            filtros['q'] = q
        if estado:
            qs = qs.filter(estado=estado)
            filtros['estado'] = estado
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
            filtros['plan_id'] = plan_id
        if renovacion in ('1', '0'):
            qs = qs.filter(renovacion_automatica=(renovacion == '1'))
            filtros['renovacion'] = renovacion
        self.filtros = filtros
        return qs.order_by('-fecha_inicio')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Suscripciones'
        ctx['filtros'] = self.filtros
        ctx['planes'] = Plan.objects.filter(activo=True).order_by('orden')
        ctx['estados'] = list(EstadoSuscripcionChoices.choices)
        ctx['_estado_sus_color'] = _estado_sus_color
        # KPIs del módulo
        ahora = timezone.now()
        ctx['total'] = Suscripcion.objects.count()
        ctx['total_activas'] = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.ACTIVA).count()
        ctx['total_pendientes'] = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.PENDIENTE).count()
        ctx['total_vencidas'] = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.VENCIDA).count()
        ctx['total_canceladas'] = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.CANCELADA).count()
        ctx['vencen_7d'] = Suscripcion.objects.filter(
            estado=EstadoSuscripcionChoices.ACTIVA,
            fecha_vencimiento__lte=ahora + timezone.timedelta(days=7),
            fecha_vencimiento__gte=ahora,
        ).count()
        return ctx


class AdminPanelSuscripcionDetailView(AdminSoporteRequiredMixin, DetailView):
    template_name = 'admin_panel/suscripcion_detalle.html'
    model = Suscripcion
    context_object_name = 'sus'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Suscripcion.objects.select_related('negocio', 'negocio__dueño', 'negocio__comuna', 'plan')
            .prefetch_related('pagos', 'cambios_plan__realizado_por'),
            pk=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Suscripciones'
        ctx['_estado_sus_color'] = _estado_sus_color
        ctx['_estado_pago_color'] = _estado_pago_color
        sus = ctx['sus']
        # Calcular monto actual usando desglose_mensual (metodología)
        cant_locales = sus.negocio.locales.filter(estado='ACTIVO').count() if sus.negocio else 0
        ctx['cant_locales_actual'] = cant_locales
        ctx['desglose'] = sus.plan.desglose_mensual(cant_locales) if sus.plan else {}
        # Feature flags del plan
        if sus.plan:
            ctx['feature_flags'] = [
                ('Benchmarking Rubro (Google)', sus.plan.tiene_benchmark_google),
                ('Análisis Reseñas Google', sus.plan.tiene_analisis_google),
                ('QR ClientBeat (NPS + CSAT)', sus.plan.tiene_qr_clientbeat),
                ('Encuestas Custom por Rubro', sus.plan.tiene_encuestas_custom_rubro),
                ('Encuestas Custom Pro (max 5)', sus.plan.tiene_encuestas_custom),
                ('Preguntas Adicionales', sus.plan.max_preguntas_adicionales or 0),
                ('Segmentación Demográfica', sus.plan.tiene_segmentacion_demografica),
                ('Benchmark ClientBeat Propio', sus.plan.tiene_benchmark_clientbeat),
                ('Notificaciones', sus.plan.tiene_notificaciones),
                ('Exportar Excel / CSV', sus.plan.tiene_export_excel),
                ('Benchmarking Rubro Plan Antiguo (flag)', sus.plan.tiene_benchmarking_rubro),
            ]
        ctx['planes'] = Plan.objects.filter(activo=True).order_by('orden')
        ctx['cambios_plan'] = sus.cambios_plan.select_related('plan_anterior', 'plan_nuevo', 'realizado_por').order_by('-fecha_cambio').all()
        return ctx


@method_decorator(require_POST, name='dispatch')
class AdminPanelSuscripcionConfirmarView(AdminSoporteRequiredMixin, View):
    """Confirmar suscripción manual: pasar PENDIENTE → ACTIVA + extender fecha vencimiento."""
    def post(self, request, pk):
        sus = get_object_or_404(Suscripcion, pk=pk)
        datos_antes = {'estado': sus.estado, 'fecha_inicio': str(sus.fecha_inicio), 'fecha_vencimiento': str(sus.fecha_vencimiento)}
        notas = request.POST.get('notas', '').strip()
        dias = int(request.POST.get('dias', sus.plan.dias_prueba_gratis if sus.plan else 30))
        ahora = timezone.now()
        sus.estado = EstadoSuscripcionChoices.ACTIVA
        sus.fecha_inicio = ahora
        sus.fecha_vencimiento = ahora + timezone.timedelta(days=dias)
        sus.save()
        # Registrar pago manual si no hay
        if not Pago.objects.filter(suscripcion=sus, estado=EstadoPagoChoices.APROBADO).exists():
            cant_locales = sus.negocio.locales.count() if sus.negocio else 0
            Pago.objects.create(
                suscripcion=sus,
                flow_order_id=f'MANUAL-{sus.id}-{ahora:%Y%m%d%H%M%S}',
                monto=sus.plan.calcular_monto_mensual(cant_locales) if sus.plan else 0,
                moneda='CLP',
                estado=EstadoPagoChoices.APROBADO,
                fecha_pago=ahora,
                comprobante_url='',
                datos_webhook={'confirmado_por': request.user.email, 'manual': True, 'notas': notas},
                firma_validada=True,
            )
        _auditar(
            request, AccionAuditoriaChoices.CONFIRMAR, ModuloAuditoriaChoices.SUSCRIPCIONES, sus,
            descripcion=f'Confirmar suscripción: {sus.negocio.nombre if sus.negocio else sus.id} ({dias} días)',
            datos_antes=datos_antes,
            datos_despues={'estado': sus.estado, 'fecha_inicio': str(sus.fecha_inicio), 'fecha_vencimiento': str(sus.fecha_vencimiento), 'dias': dias},
            notas=notas or None,
        )
        messages.success(request, f'✅ Suscripción confirmada + {dias} días. Pago manual registrado.')
        return redirect('adminpanel:suscripcion_detalle', pk=pk)


@method_decorator(require_POST, name='dispatch')
class AdminPanelSuscripcionCancelarView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        sus = get_object_or_404(Suscripcion, pk=pk)
        datos_antes = {'estado': sus.estado, 'cancelada_en': str(sus.cancelada_en), 'motivo_cancelacion': sus.motivo_cancelacion}
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, '❌ Debes ingresar un motivo de cancelación.')
            return redirect('adminpanel:suscripcion_detalle', pk=pk)
        sus.estado = EstadoSuscripcionChoices.CANCELADA
        sus.cancelada_en = timezone.now()
        sus.renovacion_automatica = False
        sus.motivo_cancelacion = motivo[:255]
        sus.save()
        _auditar(
            request, AccionAuditoriaChoices.CANCELAR, ModuloAuditoriaChoices.SUSCRIPCIONES, sus,
            descripcion=f'Cancelar suscripción: {sus.negocio.nombre if sus.negocio else sus.id} — {motivo[:80]}',
            datos_antes=datos_antes,
            datos_despues={'estado': sus.estado, 'cancelada_en': str(sus.cancelada_en), 'motivo_cancelacion': sus.motivo_cancelacion},
            notas=motivo,
        )
        messages.success(request, '❌ Suscripción cancelada correctamente.')
        return redirect('adminpanel:suscripcion_detalle', pk=pk)


@method_decorator(require_POST, name='dispatch')
class AdminPanelSuscripcionExtenderView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        sus = get_object_or_404(Suscripcion, pk=pk)
        try:
            dias = max(1, int(request.POST.get('dias', '0')))
        except ValueError:
            messages.error(request, '❌ Días inválidos.')
            return redirect('adminpanel:suscripcion_detalle', pk=pk)
        notas = request.POST.get('notas', '').strip()
        datos_antes = {'fecha_vencimiento': str(sus.fecha_vencimiento)}
        sus.fecha_vencimiento = sus.fecha_vencimiento + timezone.timedelta(days=dias)
        sus.save()
        _auditar(
            request, AccionAuditoriaChoices.EXTENDER_DIAS, ModuloAuditoriaChoices.SUSCRIPCIONES, sus,
            descripcion=f'Extender {dias} días suscripción {sus.negocio.nombre if sus.negocio else sus.id}',
            datos_antes=datos_antes, datos_despues={'fecha_vencimiento': str(sus.fecha_vencimiento), 'dias': dias},
            notas=notas or None,
        )
        messages.success(request, f'⏱️ Fecha de vencimiento extendida {dias} días. Nueva: {sus.fecha_vencimiento:%d/%m/%Y}')
        return redirect('adminpanel:suscripcion_detalle', pk=pk)


@method_decorator(require_POST, name='dispatch')
class AdminPanelSuscripcionCambiarPlanView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        sus = get_object_or_404(Suscripcion.objects.select_related('plan', 'negocio'), pk=pk)
        plan_nuevo = get_object_or_404(Plan, pk=request.POST.get('plan_nuevo_id'))
        motivo = request.POST.get('motivo', '') or MotivoCambioPlanChoices.CORRECION_ADMIN
        notas = request.POST.get('notas', '').strip()
        try:
            motivo = MotivoCambioPlanChoices[motivo]
        except Exception:
            motivo = MotivoCambioPlanChoices.CORRECION_ADMIN
        cant_locales = sus.negocio.locales.count() if sus.negocio else 0
        precio_antes = sus.plan.calcular_monto_mensual(cant_locales) if sus.plan else 0
        precio_despues = plan_nuevo.calcular_monto_mensual(cant_locales)
        plan_anterior = sus.plan
        datos_antes = {'plan_id': str(sus.plan.id), 'plan_nombre': sus.plan.nombre, 'estado': sus.estado}
        sus.plan = plan_nuevo
        if sus.estado == EstadoSuscripcionChoices.CANCELADA:
            sus.estado = EstadoSuscripcionChoices.ACTIVA
        sus.save()
        cambio = CambioPlan.objects.create(
            suscripcion=sus,
            plan_anterior=plan_anterior,
            plan_nuevo=plan_nuevo,
            motivo=motivo,
            notas=notas or None,
            precio_antes_clp=precio_antes,
            precio_despues_clp=precio_despues,
            dias_prorrateo=0,
            realizado_por=request.user,
        )
        _auditar(
            request, AccionAuditoriaChoices.CAMBIAR_PLAN, ModuloAuditoriaChoices.SUSCRIPCIONES, sus,
            descripcion=f'Cambio plan {plan_anterior.nombre} → {plan_nuevo.nombre} (${precio_antes:,} → ${precio_despues:,})',
            datos_antes=datos_antes,
            datos_despues={'plan_id': str(plan_nuevo.id), 'plan_nombre': plan_nuevo.nombre, 'cambio_plan_id': str(cambio.id)},
            notas=notas or None,
        )
        messages.success(request, f'🔀 Plan cambiado a {plan_nuevo.get_nombre_mostrar()}. Registrado CambioPlan #{str(cambio.id)[:8]}…')
        return redirect('adminpanel:suscripcion_detalle', pk=pk)


class AdminPanelSuscripcionNuevaView(AdminSoporteRequiredMixin, View):
    """Asignar plan manualmente a un negocio (crear Suscripcion PENDIENTE)."""
    def get(self, request):
        ctx = {
            'menu': modulos_menu(request),
            'menu_activo': 'Suscripciones',
            'negocios': Negocio.objects.filter(estado='ACTIVO').select_related('dueño').order_by('nombre'),
            'planes': Plan.objects.filter(activo=True).order_by('orden'),
        }
        return render(request, 'admin_panel/suscripcion_nueva.html', ctx)

    def post(self, request):
        negocio_id = request.POST.get('negocio_id')
        plan_id = request.POST.get('plan_id')
        dias = request.POST.get('dias', '365')
        activar_inmediato = request.POST.get('activar_inmediato', '') == '1'
        notas = request.POST.get('notas', '').strip()
        try:
            dias = max(1, int(dias))
        except ValueError:
            dias = 365
        negocio = get_object_or_404(Negocio, pk=negocio_id)
        plan = get_object_or_404(Plan, pk=plan_id)
        ahora = timezone.now()
        estado = EstadoSuscripcionChoices.ACTIVA if activar_inmediato else EstadoSuscripcionChoices.PENDIENTE
        sus = Suscripcion.objects.create(
            negocio=negocio, plan=plan, estado=estado,
            fecha_inicio=ahora,
            fecha_vencimiento=ahora + timezone.timedelta(days=dias),
            renovacion_automatica=False,
        )
        if activar_inmediato:
            cant_locales = negocio.locales.count()
            Pago.objects.create(
                suscripcion=sus,
                flow_order_id=f'MANUAL-{sus.id}-{ahora:%Y%m%d%H%M%S}',
                monto=plan.calcular_monto_mensual(cant_locales),
                estado=EstadoPagoChoices.APROBADO,
                fecha_pago=ahora,
                datos_webhook={'creado_por': request.user.email, 'manual': True, 'notas': notas},
                firma_validada=True,
            )
        _auditar(
            request, AccionAuditoriaChoices.CREAR, ModuloAuditoriaChoices.SUSCRIPCIONES, sus,
            descripcion=f'Nueva suscripción {negocio.nombre} → {plan.nombre} ({dias} días, {estado})',
            datos_despues={'negocio_id': str(negocio.id), 'plan_id': str(plan.id), 'dias': dias, 'estado': estado},
            notas=notas or None,
        )
        messages.success(request, f'✨ Suscripción creada. Estado: {estado}.')
        return redirect('adminpanel:suscripcion_detalle', pk=sus.id)


# ==============================
# MÓDULO 2: PAGOS / COBRANZA
# ==============================
class AdminPanelPagosListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/pagos_list.html'
    model = Pago
    context_object_name = 'pagos'
    paginate_by = 20

    def get_queryset(self):
        qs = Pago.objects.select_related('suscripcion', 'suscripcion__negocio', 'suscripcion__plan').all()
        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '').strip()
        if q:
            qs = qs.filter(
                Q(flow_order_id__icontains=q) | Q(suscripcion__negocio__nombre__icontains=q)
                | Q(suscripcion__negocio__dueño__email__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        self.filtros = {'q': q, 'estado': estado}
        return qs.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Pagos'
        ctx['filtros'] = self.filtros
        ctx['estados'] = list(EstadoPagoChoices.choices)
        ahora = timezone.now()
        desde_30d = ahora - timezone.timedelta(days=30)
        aprobados_qs = Pago.objects.filter(estado=EstadoPagoChoices.APROBADO, fecha_pago__gte=desde_30d)
        total = aprobados_qs.count()
        monto = aprobados_qs.aggregate(total=Sum('monto', default=0))['total'] or 0
        ctx['total_aprobados_30d'] = total
        ctx['monto_aprobado_30d'] = monto
        ctx['ticket_medio'] = int(monto / total) if total > 0 else 0
        ctx['pendientes'] = Pago.objects.filter(estado=EstadoPagoChoices.PENDIENTE).count()
        ctx['rechazados_30d'] = Pago.objects.filter(estado=EstadoPagoChoices.RECHAZADO, fecha_creacion__gte=desde_30d).count()
        return ctx


# ==============================
# CRUD PLANES (existentes, con mejoras)
# ==============================
class AdminPanelPlanesListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/planes_list.html'
    model = Plan
    context_object_name = 'planes'
    ordering = ['orden', 'nombre']

    def get_queryset(self):
        return Plan.objects.all().prefetch_related('rubros').order_by('orden', 'nombre')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Planes'
        ctx['planes_activos'] = Plan.objects.filter(activo=True).count()
        ctx['planes_total'] = Plan.objects.count()
        ctx['default_plan'] = Plan.objects.filter(es_plan_default=True).first()
        # Contar suscripciones por plan
        sus_count = dict(
            Suscripcion.objects
            .filter(estado=EstadoSuscripcionChoices.ACTIVA)
            .values_list('plan_id')
            .annotate(total=Count('id'))
        )
        for p in ctx['planes']:
            p.suscripciones_activas = sus_count.get(p.id, 0)
        # Historial cambios plan globales
        ctx['cambios_plan_global'] = CambioPlan.objects.select_related(
            'suscripcion', 'suscripcion__negocio', 'plan_anterior', 'plan_nuevo', 'realizado_por'
        ).order_by('-fecha_cambio')[:15]
        return ctx


class AdminPanelPlanCreateView(AdminSoporteRequiredMixin, CreateView):
    template_name = 'admin_panel/planes_form.html'
    model = Plan
    form_class = PlanForm
    success_url = reverse_lazy('adminpanel:planes')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Planes'
        ctx['modo'] = 'crear'
        return ctx

    def form_valid(self, form):
        plan = form.save(commit=False)
        if plan.es_plan_default:
            Plan.objects.filter(es_plan_default=True).update(es_plan_default=False)
        plan.save()
        form.save_m2m()
        _auditar(
            self.request, AccionAuditoriaChoices.CREAR, ModuloAuditoriaChoices.PLANES, plan,
            descripcion=f'Crear plan {plan.nombre}',
            datos_despues={'nombre': plan.nombre, 'precio_clp': plan.precio_clp, 'orden': plan.orden},
        )
        messages.success(self.request, f'Plan "{plan.nombre}" creado exitosamente.')
        return super().form_valid(form)


class AdminPanelPlanUpdateView(AdminSoporteRequiredMixin, UpdateView):
    template_name = 'admin_panel/planes_form.html'
    model = Plan
    form_class = PlanForm
    success_url = reverse_lazy('adminpanel:planes')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Planes'
        ctx['modo'] = 'editar'
        return ctx

    def form_valid(self, form):
        plan = form.save(commit=False)
        datos_antes = {f: getattr(form.initial.get('instance', plan), f) for f in form.cleaned_data if f in form.initial}
        if plan.es_plan_default:
            Plan.objects.filter(es_plan_default=True).exclude(pk=plan.pk).update(es_plan_default=False)
        plan.save()
        form.save_m2m()
        _auditar(
            self.request, AccionAuditoriaChoices.EDITAR, ModuloAuditoriaChoices.PLANES, plan,
            descripcion=f'Editar plan {plan.nombre}',
            datos_antes=datos_antes,
            datos_despues={f: form.cleaned_data.get(f) for f in form.cleaned_data},
        )
        messages.success(self.request, f'Plan "{plan.nombre}" actualizado correctamente.')
        return super().form_valid(form)


@method_decorator(require_POST, name='dispatch')
class AdminPanelPlanToggleActivoView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        if plan.activo and plan.es_plan_default:
            messages.error(request, f'No puedes desactivar el plan default ({plan.nombre}). Marca otro plan como default primero.')
            return redirect('adminpanel:planes')
        datos_antes = {'activo': plan.activo}
        with transaction.atomic():
            plan.activo = not plan.activo
            plan.save()
        _auditar(
            request,
            AccionAuditoriaChoices.ACTIVAR if plan.activo else AccionAuditoriaChoices.DESACTIVAR,
            ModuloAuditoriaChoices.PLANES, plan,
            descripcion=f'{"Activar" if plan.activo else "Desactivar"} plan {plan.nombre}',
            datos_antes=datos_antes, datos_despues={'activo': plan.activo},
        )
        estado = 'activado' if plan.activo else 'desactivado'
        messages.success(request, f'Plan "{plan.nombre}" {estado} exitosamente.')
        return redirect('adminpanel:planes')


@method_decorator(require_POST, name='dispatch')
class AdminPanelPlanMarcarDefaultView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        if not plan.activo:
            messages.error(request, f'No puedes marcar como default un plan inactivo ({plan.nombre}). Actívalo primero.')
            return redirect('adminpanel:planes')
        with transaction.atomic():
            Plan.objects.all().update(es_plan_default=False)
            plan.es_plan_default = True
            plan.save()
        _auditar(
            request, AccionAuditoriaChoices.MARCAR_DEFAULT, ModuloAuditoriaChoices.PLANES, plan,
            descripcion=f'Marcar default: {plan.nombre}',
            datos_despues={'es_plan_default': True},
        )
        messages.success(request, f'Plan "{plan.nombre}" ahora es el plan default de onboarding.')
        return redirect('adminpanel:planes')


# ==============================
# SIMULADOR DE PRECIOS PLANES
# ==============================
class AdminPanelSimuladorPlanesView(AdminSoporteRequiredMixin, TemplateView):
    template_name = 'admin_panel/simulador_planes.html'

    def get(self, request, *args, **kwargs):
        planes = Plan.objects.filter(activo=True).order_by('orden')
        ctx = self.get_context_data(**kwargs)
        ctx['planes'] = planes
        # Parámetros simulación
        try:
            cant_locales = max(1, int(request.GET.get('locales', '3')))
        except ValueError:
            cant_locales = 3
        try:
            cant_rubros = max(0, int(request.GET.get('rubros_online', '0')))
        except ValueError:
            cant_rubros = 0
        ctx['cant_locales'] = cant_locales
        ctx['cant_rubros'] = cant_rubros
        # Calcular para cada plan
        filas = []
        for p in planes:
            d = p.desglose_mensual(cant_locales, cant_rubros)
            filas.append({
                'plan': p,
                'desglose': d,
                'total_formateado': f"${d['total_clp']:,}".replace(',', '.'),
                'flags': [
                    ('Google Análisis', p.tiene_analisis_google),
                    ('Google Benchmark', p.tiene_benchmark_google),
                    ('QR ClientBeat', p.tiene_qr_clientbeat),
                    ('Encuestas Rubro', p.tiene_encuestas_custom_rubro),
                    ('Encuestas Custom Pro', p.tiene_encuestas_custom),
                    ('Benchmark CB', p.tiene_benchmark_clientbeat),
                    ('Segmentación Dem.', p.tiene_segmentacion_demografica),
                    ('Notificaciones', p.tiene_notificaciones),
                    ('Export Excel', p.tiene_export_excel),
                    ('Benchmark Rubro (legacy)', p.tiene_benchmarking_rubro),
                    (f'Preg. Adicionales: {p.max_preguntas_adicionales or 0}', bool(p.max_preguntas_adicionales)),
                ],
            })
        ctx['filas'] = filas
        if filas:
            ctx['flags_titulos'] = [f[0] for f in filas[0]['flags']]
        else:
            ctx['flags_titulos'] = []
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Simulador'
        return ctx


# ==============================
# MÓDULO 3: NEGOCIOS / CLIENTES
# ==============================
class AdminPanelNegociosListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/negocios_list.html'
    model = Negocio
    context_object_name = 'negocios'
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Negocio.objects.select_related('dueño', 'comuna', 'rubro')
            .annotate(
                cant_locales=Count('locales', distinct=True),
                cant_miembros=Count('miembros_equipo', distinct=True),
            )
            .prefetch_related('suscripciones')
        )
        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '').strip()
        onboarding = self.request.GET.get('onboarding', '').strip()
        rubro_id = self.request.GET.get('rubro', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(rut__icontains=q) | Q(dueño__email__icontains=q)
                | Q(dueño__first_name__icontains=q) | Q(dueño__last_name__icontains=q)
                | Q(razon_social__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        if onboarding == 'completo':
            qs = qs.filter(onboarding_paso1_completo=True, onboarding_paso2_completo=True, onboarding_paso3_completo=True)
        elif onboarding == 'incompleto':
            qs = qs.filter(Q(onboarding_paso1_completo=False) | Q(onboarding_paso2_completo=False) | Q(onboarding_paso3_completo=False))
        if rubro_id:
            qs = qs.filter(rubro_id=rubro_id)
        self.filtros = {'q': q, 'estado': estado, 'onboarding': onboarding, 'rubro_id': rubro_id}
        return qs.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Negocios'
        ctx['filtros'] = self.filtros
        ctx['estados_negocio'] = list(Negocio.EstadoChoices.choices)
        ctx['rubros'] = Rubro.objects.filter(activo=True).order_by('orden', 'nombre')
        # KPIs módulo
        ctx['total'] = Negocio.objects.count()
        ctx['total_activos'] = Negocio.objects.filter(estado='ACTIVO').count()
        ctx['onboarding_incompleto'] = Negocio.objects.filter(
            Q(onboarding_paso1_completo=False) | Q(onboarding_paso2_completo=False) | Q(onboarding_paso3_completo=False)
        ).count()
        ctx['sin_suscripcion_activa'] = Negocio.objects.annotate(
            sus_activa=Count('suscripciones', filter=Q(suscripciones__estado=EstadoSuscripcionChoices.ACTIVA))
        ).filter(sus_activa=0).count()
        return ctx


class AdminPanelNegocioDetailView(AdminSoporteRequiredMixin, DetailView):
    template_name = 'admin_panel/negocio_detalle.html'
    model = Negocio
    context_object_name = 'negocio'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Negocio.objects.select_related('dueño', 'comuna', 'rubro', 'comuna__provincia', 'comuna__provincia__region')
            .prefetch_related('locales__comuna', 'suscripciones__plan', 'miembros_equipo__usuario'),
            pk=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Negocios'
        ctx['suscripcion_activa'] = ctx['negocio'].suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).first()
        ctx['suscripciones_historial'] = ctx['negocio'].suscripciones.select_related('plan').order_by('-fecha_inicio')
        ctx['locales'] = ctx['negocio'].locales.select_related('comuna').all()
        ctx['miembros_equipo'] = ctx['negocio'].miembros_equipo.select_related('usuario').all()
        # Últimas respuestas de este negocio
        try:
            from apps.encuestas.models import RespuestaEncuesta
            ctx['ultimas_respuestas'] = (
                RespuestaEncuesta.objects.filter(local__negocio=ctx['negocio'])
                .select_related('local', 'plantilla')
                .order_by('-fecha_respuesta')[:10]
            )
        except Exception:
            ctx['ultimas_respuestas'] = []
        return ctx


@method_decorator(require_POST, name='dispatch')
class AdminPanelNegocioCambiarEstadoView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        negocio = get_object_or_404(Negocio, pk=pk)
        nuevo_estado = request.POST.get('estado', '').strip()
        notas = request.POST.get('notas', '').strip()
        if nuevo_estado not in [c[0] for c in Negocio.EstadoChoices.choices]:
            messages.error(request, '❌ Estado inválido.')
            return redirect('adminpanel:negocio_detalle', pk=pk)
        datos_antes = {'estado': negocio.estado}
        negocio.estado = nuevo_estado
        negocio.save()
        accion = {
            Negocio.EstadoChoices.ACTIVO: AccionAuditoriaChoices.ACTIVAR,
            Negocio.EstadoChoices.SUSPENDIDO: AccionAuditoriaChoices.SUSPENDER,
        }.get(nuevo_estado, AccionAuditoriaChoices.EDITAR)
        _auditar(
            request, accion, ModuloAuditoriaChoices.NEGOCIOS, negocio,
            descripcion=f'Cambiar estado negocio {negocio.nombre}: {datos_antes["estado"]} → {nuevo_estado}',
            datos_antes=datos_antes, datos_despues={'estado': nuevo_estado},
            notas=notas or None,
        )
        messages.success(request, f'✅ Estado actualizado a {negocio.get_estado_display()}.')
        return redirect('adminpanel:negocio_detalle', pk=pk)


@method_decorator(require_POST, name='dispatch')
class AdminPanelNegocioReiniciarOnboardingView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        negocio = get_object_or_404(Negocio, pk=pk)
        paso = request.POST.get('paso', 'todos').strip()
        notas = request.POST.get('notas', '').strip()
        datos_antes = {
            'onboarding_paso1_completo': negocio.onboarding_paso1_completo,
            'onboarding_paso2_completo': negocio.onboarding_paso2_completo,
            'onboarding_paso3_completo': negocio.onboarding_paso3_completo,
        }
        with transaction.atomic():
            if paso == 'todos' or paso == '1':
                negocio.onboarding_paso1_completo = False
                negocio.onboarding_fecha_paso1 = None
            if paso == 'todos' or paso == '2':
                negocio.onboarding_paso2_completo = False
                negocio.onboarding_fecha_paso2 = None
            if paso == 'todos' or paso == '3':
                negocio.onboarding_paso3_completo = False
                negocio.onboarding_fecha_paso3 = None
            negocio.save()
        _auditar(
            request, AccionAuditoriaChoices.REINICIAR_ONBOARDING, ModuloAuditoriaChoices.NEGOCIOS, negocio,
            descripcion=f'Reiniciar onboarding ({paso}) de {negocio.nombre}',
            datos_antes=datos_antes,
            datos_despues={
                'onboarding_paso1_completo': negocio.onboarding_paso1_completo,
                'onboarding_paso2_completo': negocio.onboarding_paso2_completo,
                'onboarding_paso3_completo': negocio.onboarding_paso3_completo,
            },
            notas=f'Paso reiniciado: {paso}. {notas}' if notas else f'Paso reiniciado: {paso}',
        )
        messages.success(request, f'♻️ Onboarding reiniciado ({paso}). El dueño podrá rehacerlo al iniciar sesión.')
        return redirect('adminpanel:negocio_detalle', pk=pk)


@method_decorator(require_POST, name='dispatch')
class AdminPanelNegocioReasignarDuenoView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        negocio = get_object_or_404(Negocio.objects.select_related('dueño'), pk=pk)
        nuevo_dueno = get_object_or_404(User, pk=request.POST.get('nuevo_dueno_id'))
        notas = request.POST.get('notas', '').strip()
        if negocio.dueño_id == nuevo_dueno.id:
            messages.error(request, '❌ El nuevo dueño ya es el mismo actual.')
            return redirect('adminpanel:negocio_detalle', pk=pk)
        datos_antes = {'dueno_id': str(negocio.dueño_id), 'dueno_email': negocio.dueño.email}
        viejo_dueno = negocio.dueño
        with transaction.atomic():
            negocio.dueño = nuevo_dueno
            negocio.save()
            # También reemplazar miembro equipo
            MiembroEquipo.objects.filter(negocio=negocio, usuario=nuevo_dueno).delete()
            MiembroEquipo.objects.update_or_create(
                negocio=negocio, usuario=nuevo_dueno,
                defaults={'rol': MiembroEquipo.RolChoices.DUENO, 'estado': 'ACTIVO', 'invitado_por': request.user}
            )
        _auditar(
            request, AccionAuditoriaChoices.REASIGNAR_DUENO, ModuloAuditoriaChoices.NEGOCIOS, negocio,
            descripcion=f'Reasignar dueño de {negocio.nombre}: {viejo_dueno.email} → {nuevo_dueno.email}',
            datos_antes=datos_antes,
            datos_despues={'dueno_id': str(nuevo_dueno.id), 'dueno_email': nuevo_dueno.email},
            notas=notas or None,
        )
        messages.success(request, f'🔀 Dueño reasignado: {nuevo_dueno.email}.')
        return redirect('adminpanel:negocio_detalle', pk=pk)


class AdminPanelUsuariosListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/usuarios_list.html'
    model = User
    context_object_name = 'usuarios'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.all().order_by('-fecha_creacion')
        q = self.request.GET.get('q', '').strip()
        rol = self.request.GET.get('rol', '').strip()
        activo = self.request.GET.get('activo', '').strip()
        if q:
            qs = qs.filter(
                Q(email__icontains=q) | Q(username__icontains=q)
                | Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
        if rol:
            qs = qs.filter(rol=rol)
        if activo in ('1', '0'):
            qs = qs.filter(is_active=(activo == '1'))
        self.filtros = {'q': q, 'rol': rol, 'activo': activo}
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Usuarios'
        ctx['filtros'] = self.filtros
        ctx['roles'] = list(User.RolChoices.choices)
        ctx['total'] = User.objects.count()
        ctx['admin_soporte'] = User.objects.filter(rol=User.RolChoices.ADMIN_SOPORTE, is_active=True).count()
        ctx['duenos'] = User.objects.filter(rol=User.RolChoices.DUENO, is_active=True).count()
        ctx['usuarios_equipo'] = User.objects.filter(rol=User.RolChoices.USUARIO_EQUIPO, is_active=True).count()
        ctx['inactivos'] = User.objects.filter(is_active=False).count()
        return ctx


@method_decorator(require_POST, name='dispatch')
class AdminPanelUsuarioCambiarRolView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        if usuario.is_superuser and not request.user.is_superuser:
            messages.error(request, '❌ No puedes cambiar el rol de un SuperUser.')
            return redirect('adminpanel:usuarios')
        nuevo_rol = request.POST.get('rol', '').strip()
        if nuevo_rol not in [c[0] for c in User.RolChoices.choices]:
            messages.error(request, '❌ Rol inválido.')
            return redirect('adminpanel:usuarios')
        datos_antes = {'rol': usuario.rol}
        usuario.rol = nuevo_rol
        usuario.save()
        _auditar(
            request, AccionAuditoriaChoices.CAMBIAR_ROL, ModuloAuditoriaChoices.USUARIOS, usuario,
            descripcion=f'Cambiar rol {usuario.email}: {datos_antes["rol"]} → {nuevo_rol}',
            datos_antes=datos_antes, datos_despues={'rol': nuevo_rol},
        )
        messages.success(request, f'✅ Rol actualizado a {usuario.get_rol_display()}.')
        return redirect('adminpanel:usuarios')


@method_decorator(require_POST, name='dispatch')
class AdminPanelUsuarioCambiarEstadoView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        if usuario.is_superuser and not request.user.is_superuser:
            messages.error(request, '❌ No puedes desactivar a un SuperUser.')
            return redirect('adminpanel:usuarios')
        datos_antes = {'is_active': usuario.is_active}
        usuario.is_active = not usuario.is_active
        usuario.save()
        _auditar(
            request,
            AccionAuditoriaChoices.ACTIVAR if usuario.is_active else AccionAuditoriaChoices.DESACTIVAR,
            ModuloAuditoriaChoices.USUARIOS, usuario,
            descripcion=f'{"Activar" if usuario.is_active else "Desactivar"} usuario {usuario.email}',
            datos_antes=datos_antes, datos_despues={'is_active': usuario.is_active},
        )
        messages.success(request, f'Usuario {"activado" if usuario.is_active else "desactivado"}.')
        return redirect('adminpanel:usuarios')


@method_decorator(require_POST, name='dispatch')
class AdminPanelUsuarioResetClaveView(AdminSoporteRequiredMixin, View):
    """Resetear clave manualmente: setea ClienBeat2026! y fuerza cambio (marca is_active + envía notas)."""
    def post(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        if usuario.is_superuser and not request.user.is_superuser:
            messages.error(request, '❌ No puedes resetear la clave de un SuperUser.')
            return redirect('adminpanel:usuarios')
        nueva = request.POST.get('nueva_clave', '').strip() or 'ClienBeat2026!'
        usuario.set_password(nueva)
        usuario.save()
        _auditar(
            request, AccionAuditoriaChoices.RESETEAR_CLAVE, ModuloAuditoriaChoices.USUARIOS, usuario,
            descripcion=f'Resetear clave usuario {usuario.email}',
            datos_despues={'long_clave': len(nueva)},
            notas='Clave reseteada manualmente por Admin Soporte.',
        )
        messages.success(request, f'🔑 Clave reseteada. Nueva: <code>{nueva}</code>')
        return redirect('adminpanel:usuarios')


# ==============================
# Plantillas Encuestas (existentes + mejora: duplicar)
# ==============================
class AdminPanelPlantillasListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/plantillas_list.html'
    model = PlantillaEncuesta
    context_object_name = 'plantillas'
    ordering = ['orden', 'nombre']

    def get_queryset(self):
        return (
            PlantillaEncuesta.objects.all()
            .prefetch_related('rubros')
            .annotate(total_respuestas=Count('respuestas'))
            .order_by('orden', 'nombre')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Plantillas Encuestas'
        ctx['total_plantillas'] = PlantillaEncuesta.objects.count()
        ctx['plantillas_activas'] = PlantillaEncuesta.objects.filter(activa=True).count()
        ctx['default'] = PlantillaEncuesta.objects.filter(es_default=True).first()
        return ctx


@method_decorator(require_POST, name='dispatch')
class AdminPanelPlantillaToggleActivaView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        plant = get_object_or_404(PlantillaEncuesta, pk=pk)
        if plant.es_default and plant.activa:
            messages.error(request, 'No puedes desactivar la plantilla default. Marca otra como default primero.')
            return redirect('adminpanel:plantillas')
        datos_antes = {'activa': plant.activa}
        plant.activa = not plant.activa
        plant.save()
        _auditar(
            request,
            AccionAuditoriaChoices.ACTIVAR if plant.activa else AccionAuditoriaChoices.DESACTIVAR,
            ModuloAuditoriaChoices.PLANTILLAS_ENCUESTAS, plant,
            descripcion=f'{"Activar" if plant.activa else "Desactivar"} plantilla {plant.nombre}',
            datos_antes=datos_antes, datos_despues={'activa': plant.activa},
        )
        estado = 'activada' if plant.activa else 'desactivada'
        messages.success(request, f'Plantilla "{plant.nombre}" {estado} exitosamente.')
        return redirect('adminpanel:plantillas')


@method_decorator(require_POST, name='dispatch')
class AdminPanelPlantillaMarcarDefaultView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        plant = get_object_or_404(PlantillaEncuesta, pk=pk)
        if not plant.activa:
            messages.error(request, 'No puedes marcar como default una plantilla inactiva. Actívala primero.')
            return redirect('adminpanel:plantillas')
        with transaction.atomic():
            PlantillaEncuesta.objects.all().update(es_default=False)
            plant.es_default = True
            plant.save()
        _auditar(
            request, AccionAuditoriaChoices.MARCAR_DEFAULT, ModuloAuditoriaChoices.PLANTILLAS_ENCUESTAS, plant,
            descripcion=f'Marcar default plantilla {plant.nombre}',
            datos_despues={'es_default': True},
        )
        messages.success(request, f'Ahora la plantilla default es: "{plant.nombre}"')
        return redirect('adminpanel:plantillas')


@method_decorator(require_POST, name='dispatch')
class AdminPanelPlantillaDuplicarView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        original = get_object_or_404(PlantillaEncuesta.objects.prefetch_related('rubros'), pk=pk)
        import secrets
        copia = PlantillaEncuesta.objects.create(
            nombre=f'{original.nombre} (Copia {secrets.token_hex(2).upper()})',
            descripcion=original.descripcion,
            contenido=original.contenido,
            estructura_json=original.estructura_json,
            tipo=original.tipo,
            orden=original.orden + 1,
            activa=False,
            es_default=False,
        )
        for rubro in original.rubros.all():
            copia.rubros.add(rubro)
        _auditar(
            request, AccionAuditoriaChoices.CREAR, ModuloAuditoriaChoices.PLANTILLAS_ENCUESTAS, copia,
            descripcion=f'Duplicar plantilla desde #{str(original.id)[:8]}: {original.nombre} → {copia.nombre}',
            datos_despues={'origen_id': str(original.id)},
        )
        messages.success(request, f'📋 Plantilla duplicada. Nueva: "{copia.nombre}" (inactiva, revisa antes de activar).')
        return redirect('adminpanel:plantillas')


# ==============================
# Plantillas Notificaciones
# ==============================
class AdminPanelPlantillasNotifListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/plantillas_notif_list.html'
    context_object_name = 'plantillas'

    def get_queryset(self):
        from apps.notifications.models import PlantillaNotificacion, CategoriaNotificacionChoices
        qs = PlantillaNotificacion.objects.all()
        cat = self.request.GET.get('cat', '').strip()
        if cat:
            qs = qs.filter(categoria=cat)
        self.filtros = {'cat': cat}
        return qs.order_by('categoria', 'orden', 'nombre')

    def get_context_data(self, **kwargs):
        from apps.notifications.models import CategoriaNotificacionChoices
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Plantillas Notif'
        ctx['filtros'] = self.filtros
        ctx['categorias'] = list(CategoriaNotificacionChoices.choices)
        # Totales por categoría
        from apps.notifications.models import PlantillaNotificacion
        tots = {}
        for ck, cl in CategoriaNotificacionChoices.choices:
            tots[ck] = {
                'label': cl,
                'total': PlantillaNotificacion.objects.filter(categoria=ck).count(),
                'activas': PlantillaNotificacion.objects.filter(categoria=ck, activo=True).count(),
            }
        ctx['categorias_totales'] = tots
        return ctx


@method_decorator(require_POST, name='dispatch')
class AdminPanelPlantillaNotifToggleActivaView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        from apps.notifications.models import PlantillaNotificacion
        plant = get_object_or_404(PlantillaNotificacion, pk=pk)
        plant.activo = not plant.activo
        plant.save()
        _auditar(
            request,
            AccionAuditoriaChoices.ACTIVAR if plant.activo else AccionAuditoriaChoices.DESACTIVAR,
            ModuloAuditoriaChoices.PLANTILLAS_NOTIFICACIONES, plant,
            descripcion=f'{"Activar" if plant.activo else "Desactivar"} plantilla notif {plant.codigo_unico}',
            datos_antes={'activo': not plant.activo}, datos_despues={'activo': plant.activo},
        )
        estado = 'activada' if plant.activo else 'desactivada'
        messages.success(request, f'Plantilla notificación "{plant.nombre}" {estado}.')
        return redirect('adminpanel:plantillas_notificaciones')


class AdminPanelRubrosListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/rubros_list.html'
    model = Rubro
    context_object_name = 'rubros'
    ordering = ['orden', 'nombre']

    def get_queryset(self):
        qs = Rubro.objects.annotate(
            total_negocios=Count('negocios', distinct=True),
            total_planes=Count('planes', distinct=True),
        )
        q = self.request.GET.get('q', '').strip()
        tipo = self.request.GET.get('tipo', '').strip()
        activo = self.request.GET.get('activo', '').strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(slug__icontains=q))
        if tipo:
            qs = qs.filter(tipo=tipo)
        if activo in ('1', '0'):
            qs = qs.filter(activo=(activo == '1'))
        self.filtros = {'q': q, 'tipo': tipo, 'activo': activo}
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Rubros'
        ctx['filtros'] = self.filtros
        ctx['tipos_rubro'] = [(r[0], r[1]) for r in Rubro.TipoRubroChoices.choices] if hasattr(Rubro, 'TipoRubroChoices') else []
        try:
            ctx['tipos_rubro'] = list(Rubro.TIPO_CHOICES) if hasattr(Rubro, 'TIPO_CHOICES') else ctx['tipos_rubro']
        except Exception:
            pass
        total_rubros = Rubro.objects.count()
        activos_rubros = Rubro.objects.filter(activo=True).count()
        ctx['total'] = total_rubros
        ctx['activos'] = activos_rubros
        ctx['inactivos'] = total_rubros - activos_rubros
        return ctx


@method_decorator(require_POST, name='dispatch')
class AdminPanelRubroToggleActivoView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        r = get_object_or_404(Rubro, pk=pk)
        datos_antes = {'activo': r.activo}
        r.activo = not r.activo
        r.save()
        _auditar(
            request,
            AccionAuditoriaChoices.ACTIVAR if r.activo else AccionAuditoriaChoices.DESACTIVAR,
            ModuloAuditoriaChoices.RUBROS, r,
            descripcion=f'{"Activar" if r.activo else "Desactivar"} rubro {r.nombre}',
            datos_antes=datos_antes, datos_despues={'activo': r.activo},
        )
        estado = 'activado' if r.activo else 'desactivado'
        messages.success(request, f'Rubro "{r.nombre}" {estado}.')
        return redirect('adminpanel:rubros')


# ==============================
# METODOLOGÍA DE CÁLCULOS
# ==============================
class AdminPanelMetodologiaView(AdminSoporteRequiredMixin, TemplateView):
    template_name = 'admin_panel/metodologia.html'

    def get(self, request, *args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        negocio_id = request.GET.get('negocio', '').strip()
        local_id = request.GET.get('local', '').strip()
        ctx['negocio_id'] = negocio_id
        ctx['local_id'] = local_id

        # Negocios select
        ctx['negocios'] = Negocio.objects.filter(estado='ACTIVO').order_by('nombre')

        metodologia = {
            'formulas': [
                ('NPS (Net Promoter Score)',
                 'NPS = % Promotores (9-10) - % Detractores (0-6)',
                 'Prom = (promotores / total) * 100 - (detractores / total) * 100',
                 'Rango [-100, +100]. Clasificación: ≥50 Promotor, 0-49 Pasivo, <0 Detractor.'),
                ('CSAT (Customer Satisfaction)',
                 '% CSAT Felices = (respuestas 😊 Muy_Satisfecho / total CSAT) × 100',
                 'Opciones 😊 Muy_Satisfecho | 🙂 Satisfecho | 😐 Neutral | 😞 Insatisfecho | 😠 Muy_Insatisfecho',
                 'Puede verse por emoción y con % Netos = Felices - Insatisfechos.'),
                ('Costo mensual Suscripción',
                 'Total = precio_base + max(0, locales - locales_gratis_incluidos) × costo_local + max(0, rubros - rubros_gratis) × costo_rubro',
                 'Método: Plan.calcular_monto_mensual(cant_locales, cant_rubros) → int',
                 'Cada plan define los umbrales "gratis incluidos" y costo extra escalonado.'),
                ('Latencia entre respuestas',
                 'Δt = fecha_respuesta[i] - fecha_respuesta[i-1] (solo n-1 intervalos)',
                 'Promedio = mean(Δt). Hora pico = moda hora (con hora local Chile). Día pico = moda weekday (Lun..Dom).',
                 'Se usan fechas localizadas (no UTC) para picos.'),
                ('Análisis Temáticas 4D',
                 'Bag-of-words keyword-based (no ML). 4 dimensiones Atención / Producto / Espacio / Limpieza.',
                 'Cada comentario puede pertenecer a múltiples dimensiones (conteo menciones, no porcentaje sobre comentarios).',
                 'Modismos chilenos: "lento","rápido","rico","baño sucio","acogedor","amable","caro","rico", etc.'),
                ('Benchmark Plan (feature flags)',
                 '7 flags: Google Análisis, Google Benchmark, QR ClientBeat, Encuestas Rubro, Encuestas Custom Pro, Segmentación Demográfica, Benchmark ClientBeat.',
                 'Plan Profesional = Todo activo + 3 preg. adicionales. Plan Básico = Solo Google. Plan2 = Google + QR.',
                 'Se muestran en detalle Suscripción con checkmark verde/rojo y en Simulador Precios.'),
            ]
        }

        # Si hay negocio seleccionado, calcular TODO con data real (validar metodología)
        negocio = None
        local_qs = None
        if negocio_id:
            try:
                negocio = Negocio.objects.select_related('rubro').get(pk=negocio_id)
                ctx['negocio_sel'] = negocio
                # Suscripción activa (metodología cálculo precio)
                sus = negocio.suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).first()
                cant_locales = negocio.locales.filter(estado='ACTIVO').count()
                ctx['sus_activa'] = sus
                ctx['cant_locales_actual'] = cant_locales
                if sus:
                    ctx['desglose_metodologia'] = sus.plan.desglose_mensual(cant_locales)
                # Respuestas QR de este negocio
                try:
                    from apps.encuestas.models import RespuestaEncuesta, EmocionCSATChoices
                    if local_id:
                        resp_qs = RespuestaEncuesta.objects.filter(local_id=local_id, local__negocio=negocio).select_related('local')
                    else:
                        resp_qs = RespuestaEncuesta.objects.filter(local__negocio=negocio).select_related('local')
                    respuestas = list(resp_qs.order_by('fecha_respuesta'))
                    ctx['total_respuestas'] = len(respuestas)
                    # NPS
                    resp_nps = [r for r in respuestas if r.nps_puntaje is not None]
                    if resp_nps:
                        total = len(resp_nps)
                        promotores = sum(1 for r in resp_nps if r.nps_puntaje >= 9)
                        pasivos = sum(1 for r in resp_nps if r.nps_puntaje in (7, 8))
                        detractores = sum(1 for r in resp_nps if r.nps_puntaje <= 6)
                        nps_score = round(100 * (promotores - detractores) / total)
                        nps_calc_show = [
                            ('Total respuestas NPS', total),
                            ('Promotores (puntaje ≥ 9)', f'{promotores} ({round(100*promotores/total, 1)}%)'),
                            ('Pasivos (puntaje 7-8)', f'{pasivos} ({round(100*pasivos/total, 1)}%)'),
                            ('Detractores (puntaje ≤ 6)', f'{detractores} ({round(100*detractores/total, 1)}%)'),
                            ('Fórmula NPS = %P - %D', f'{round(100*promotores/total, 1)}% - {round(100*detractores/total, 1)}% = {nps_score:+d}'),
                        ]
                        ctx['nps_calc'] = nps_calc_show
                        ctx['nps_score'] = nps_score
                    # CSAT
                    resp_csat = [r for r in respuestas if r.csat_emocion]
                    if resp_csat:
                        from collections import Counter
                        c = Counter(r.csat_emocion for r in resp_csat)
                        total = len(resp_csat)
                        csat_felices = c.get(EmocionCSATChoices.MUY_SATISFECHO, 0) if hasattr(EmocionCSATChoices, 'MUY_SATISFECHO') else c.get('FELIZ', 0)
                        if not csat_felices:
                            csat_felices = c.get('FELIZ') or c.get('MUY_SATISFECHO') or 0
                        csat_pct = round(100 * csat_felices / total, 1)
                        rows = []
                        for k, lab in EmocionCSATChoices.choices:
                            cnt = c.get(k, 0)
                            rows.append((lab, cnt, round(100 * cnt / total, 1) if total else 0))
                        ctx['csat_distribucion'] = rows
                        ctx['csat_pct_felices'] = csat_pct
                        ctx['csat_total'] = total
                    # Latencia (intervalos n-1)
                    if len(respuestas) >= 2:
                        import statistics
                        deltas_min = []
                        horas = []
                        dias = []
                        dias_labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                        for i in range(1, len(respuestas)):
                            d = (respuestas[i].fecha_respuesta - respuestas[i-1].fecha_respuesta).total_seconds() / 60
                            deltas_min.append(d)
                        for r in respuestas:
                            try:
                                local_dt = timezone.localtime(r.fecha_respuesta)
                                horas.append(local_dt.hour)
                                dias.append(dias_labels[local_dt.weekday()])
                            except Exception:
                                pass
                        from collections import Counter
                        avg_min = round(statistics.mean(deltas_min), 1) if deltas_min else 0
                        horas_cnt = Counter(horas)
                        dias_cnt = Counter(dias)
                        ctx['latencia_prom_min'] = avg_min
                        ctx['latencia_prom_horas'] = round(avg_min / 60, 1)
                        ctx['dist_horas'] = sorted(horas_cnt.items(), key=lambda x: x[0])
                        ctx['dist_horas_pico'] = horas_cnt.most_common(1)[0] if horas_cnt else ('-', 0)
                        ctx['dist_dias'] = [(dl, dias_cnt.get(dl, 0)) for dl in dias_labels]
                        ctx['dist_dias_pico'] = dias_cnt.most_common(1)[0] if dias_cnt else ('-', 0)
                    # Temáticas 4D
                    if respuestas:
                        dims = {
                            'Atención al Cliente': ['atencion', 'atento', 'amable', 'rapido', 'rápido', 'lento', 'desagradable', 'grosero', 'mal atendido', 'trato', 'personal', 'mesero', 'empleado', 'cajero'],
                            'Producto / Servicio': ['sabor', 'rico', 'comida', 'bebida', 'calidad', 'caro', 'barato', 'precio', 'cantidad', 'porción', 'producto', 'servicio', 'rico rico', 'fresco', 'podrido', 'malo'],
                            'Espacio / Ambiente': ['acogedor', 'ambiente', 'lugar', 'local', 'espacio', 'comodo', 'cómodo', 'limpio ambiente', 'decoracion', 'decoración', 'musica', 'música', 'ruido', 'clima', 'frio', 'frío', 'calor'],
                            'Limpieza / Higiene': ['limpio', 'sucio', 'baño', 'higiene', 'mesa sucia', 'piso', 'polvo', 'cocina', 'vaso', 'plato', 'suciedad', 'limpieza'],
                        }
                        def cuenta_menciones(text, keywords):
                            if not text:
                                return 0
                            t = text.lower()
                            return sum(1 for kw in keywords if kw.lower() in t)
                        tematicas = []
                        total_menciones = 0
                        comentarios_analizados = 0
                        for dim, kws in dims.items():
                            menc = 0
                            for r in respuestas:
                                c = getattr(r, 'comentario', '') or ''
                                if c.strip():
                                    m = cuenta_menciones(c, kws)
                                    menc += m
                            total_menciones += menc
                            tematicas.append((dim, menc, 0))
                        tematicas = [(d, m, round(100 * m / total_menciones, 1) if total_menciones else 0) for d, m, _ in tematicas]
                        tematicas.sort(key=lambda x: -x[1])
                        comentarios_analizados = sum(1 for r in respuestas if (getattr(r, 'comentario', '') or '').strip())
                        ctx['tematicas'] = tematicas
                        ctx['tematicas_total'] = total_menciones
                        ctx['comentarios_analizados'] = comentarios_analizados
                except Exception as e_encuestas:
                    ctx['error_calculo'] = f'Error cargando módulo encuestas: {str(e_encuestas)}'
            except Exception as e:
                ctx['error_calculo'] = str(e)

        ctx['metodologia'] = metodologia
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Metodología'
        return ctx


# ==============================
# AUDITORÍA ADMIN
# ==============================
class AdminPanelAuditoriaListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/auditoria_list.html'
    model = AuditoriaAdmin
    context_object_name = 'auditorias'
    paginate_by = 25

    def get_queryset(self):
        qs = AuditoriaAdmin.objects.select_related('usuario').all()
        q = self.request.GET.get('q', '').strip()
        modulo = self.request.GET.get('modulo', '').strip()
        accion = self.request.GET.get('accion', '').strip()
        usuario_email = self.request.GET.get('usuario', '').strip()
        if q:
            qs = qs.filter(
                Q(entidad_descripcion__icontains=q) | Q(entidad_tipo__icontains=q)
                | Q(entidad_id__icontains=q) | Q(notas_internas__icontains=q)
            )
        if modulo:
            qs = qs.filter(modulo=modulo)
        if accion:
            qs = qs.filter(accion=accion)
        if usuario_email:
            qs = qs.filter(usuario_email__icontains=usuario_email)
        self.filtros = {'q': q, 'modulo': modulo, 'accion': accion, 'usuario': usuario_email}
        return qs.order_by('-fecha_hora')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Auditoría'
        ctx['filtros'] = self.filtros
        ctx['modulos'] = list(ModuloAuditoriaChoices.choices)
        ctx['acciones'] = list(AccionAuditoriaChoices.choices)
        # KPIs auditoría últimos 7 días
        ahora = timezone.now()
        desde_7d = ahora - timezone.timedelta(days=7)
        ctx['total_7d'] = AuditoriaAdmin.objects.filter(fecha_hora__gte=desde_7d).count()
        ctx['total'] = AuditoriaAdmin.objects.count()
        # Top usuarios auditoría
        top_users = (
            AuditoriaAdmin.objects.filter(fecha_hora__gte=desde_7d)
            .values('usuario_email').annotate(total=Count('id')).order_by('-total')[:8]
        )
        ctx['top_admins_7d'] = list(top_users)
        return ctx


# ==============================
# Placeholders genéricos + Super Salud
# ==============================
class PlaceholderView(AdminSoporteRequiredMixin, TemplateView):
    template_name = 'admin_panel/placeholder.html'
    titulo = 'Módulo en construcción'
    icono = 'fa-cogs'
    color = 'blue'
    descripcion = 'Este módulo se implementará próximamente con el panel no-técnico para gestionar su contenido.'

    def get_titulo(self):
        return self.titulo

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = self.get_titulo()
        ctx['placeholder_titulo'] = self.get_titulo()
        ctx['placeholder_icono'] = self.icono
        ctx['placeholder_color'] = self.color
        ctx['placeholder_descripcion'] = self.descripcion
        return ctx


class SuperSaludView(SuperUserRequiredMixin, TemplateView):
    """Solo SuperUser: estado técnico de base de datos y settings."""
    template_name = 'admin_panel/super_salud.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Salud Técnica'
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                ctx['db_ok'] = True
                ctx['db_vendor'] = connection.vendor
        except Exception as e:
            ctx['db_ok'] = False
            ctx['db_error'] = str(e)
        from django.conf import settings
        ctx['DEBUG'] = settings.DEBUG
        ctx['DATABASE_ENGINE'] = settings.DATABASES['default'].get('ENGINE', '?')
        # Conteos de migraciones aplicadas
        try:
            from django.db.migrations.recorder import MigrationRecorder
            mr = MigrationRecorder(connection)
            ctx['migrations_total'] = mr.migration_qs.count()
        except Exception:
            ctx['migrations_total'] = None
        # Celery y Redis si están configurados
        try:
            ctx['CELERY_BROKER_URL_OK'] = bool(getattr(settings, 'CELERY_BROKER_URL', None))
        except Exception:
            ctx['CELERY_BROKER_URL_OK'] = False
        ctx['INSTALLED_APPS'] = [a for a in settings.INSTALLED_APPS if a.startswith('apps.')]
        return ctx


# ==============================
# 1. REPORTERÍA VIEWS
# ==============================
class ReporteriaClientesView(AdminSoporteRequiredMixin, ListView):
    """1.1 Listado de clientes (Negocios registrados en la plataforma)."""
    template_name = 'admin_panel/reporteria/clientes.html'
    context_object_name = 'negocios'
    paginate_by = 25

    def get_queryset(self):
        qs = Negocio.objects.select_related('dueño', 'comuna', 'rubro').annotate(
            total_locales=Count('locales', distinct=True)
        ).order_by('-fecha_creacion')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(rut__icontains=q) | Q(dueño__email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'reporteria_clientes'
        ctx['seccion_titulo'] = '1.1 Listado de Clientes'
        ctx['total_clientes'] = Negocio.objects.count()
        ctx['clientes_activos'] = Negocio.objects.filter(estado='ACTIVO').count()
        return ctx


class ReporteriaBenchmarkRubroView(AdminSoporteRequiredMixin, TemplateView):
    """1.2 Benchmark por rubro."""
    template_name = 'admin_panel/reporteria/benchmark_rubro.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'reporteria_benchmark_rubro'
        ctx['rubros_stats'] = Rubro.objects.filter(activo=True).annotate(
            total_negocios=Count('negocios', distinct=True)
        ).order_by('-total_negocios')
        ctx['filtro_temporal'] = self.request.GET.get('filtro_temporal', 'MENSUAL')
        ctx['filtro_geografico'] = self.request.GET.get('filtro_geografico', 'COMUNAL')
        ctx['config_metricas'] = ConfiguracionMetricas.get_solo()
        return ctx


class ReporteriaTendenciasResenasView(AdminSoporteRequiredMixin, TemplateView):
    """1.3 Tendencias en reseñas."""
    template_name = 'admin_panel/reporteria/tendencias_resenas.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'reporteria_tendencias_resenas'
        ctx['seccion_titulo'] = '1.3 Tendencias en Reseñas'
        from apps.reputation.models import ResenaGoogle, SentimientoChoices
        ctx['total_resenas'] = ResenaGoogle.objects.count()
        ctx['positivas'] = ResenaGoogle.objects.filter(sentimiento=SentimientoChoices.POSITIVO).count()
        ctx['neutras'] = ResenaGoogle.objects.filter(sentimiento=SentimientoChoices.NEUTRO).count()
        ctx['negativas'] = ResenaGoogle.objects.filter(sentimiento=SentimientoChoices.NEGATIVO).count()
        ctx['config_metricas'] = ConfiguracionMetricas.get_solo()
        return ctx


class ReporteriaPlanesView(AdminSoporteRequiredMixin, TemplateView):
    """1.4 Planes (Por rubro, Por ubicación geográfica, Por cambios / bajas / altas)."""
    template_name = 'admin_panel/reporteria/planes.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'reporteria_planes'
        ctx['seccion_titulo'] = '1.4 Reportes de Planes'
        ctx['tab_activo'] = self.request.GET.get('tab', 'rubro')
        ctx['cambios_plan'] = CambioPlan.objects.select_related('suscripcion__negocio', 'plan_anterior', 'plan_nuevo', 'suscripcion').order_by('-fecha_cambio')[:50]
        ctx['suscripciones_activas'] = Suscripcion.objects.select_related('negocio', 'plan').filter(estado=EstadoSuscripcionChoices.ACTIVA)
        return ctx


# ==============================
# 2. DATA GOOGLE VIEWS
# ==============================
class DataGoogleRubrosView(AdminSoporteRequiredMixin, ListView):
    """2.1 Rubros y Preguntas asociadas al rubro (Google Places & Encuestas)."""
    template_name = 'admin_panel/datagoogle/rubros.html'
    context_object_name = 'rubros'
    paginate_by = 30

    def get_queryset(self):
        qs = Rubro.objects.select_related('google_category').prefetch_related('plantillas_encuesta').order_by('orden', 'nombre')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(google_category__google_es__icontains=q)
                | Q(google_category__google_en__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'datagoogle_rubros'
        ctx['seccion_titulo'] = '2.1 Rubros y Preguntas Asociadas'
        ctx['q'] = self.request.GET.get('q', '').strip()
        ctx['plantillas_encuesta'] = PlantillaEncuesta.objects.filter(activa=True)
        ctx['total_rubros'] = Rubro.objects.count()
        ctx['rubros_con_google'] = Rubro.objects.exclude(google_category__isnull=True).count()
        ctx['rubros_con_plantillas'] = Rubro.objects.annotate(cp=Count('plantillas_encuesta')).filter(cp__gt=0).count()
        ctx['rubros_activos'] = Rubro.objects.filter(activo=True).count()
        return ctx



class DataGoogleInfoNegocioView(AdminSoporteRequiredMixin, TemplateView):
    """2.2 Información general por negocio (Fase 2 - pendiente definir información a entregar)."""
    template_name = 'admin_panel/datagoogle/info_negocio.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'datagoogle_info_negocio'
        ctx['seccion_titulo'] = '2.2 Información General por Negocio'
        return ctx


# ==============================
# 3. MÉTRICAS VIEWS
# ==============================
class MetricasCriteriosBenchmarkView(AdminSoporteRequiredMixin, View):
    """3.1 Modificar criterios de Benchmark (Google y ClientBeat)."""
    template_name = 'admin_panel/metricas/criterios_benchmark.html'

    def get(self, request):
        config = ConfiguracionMetricas.get_solo()
        context = {
            'menu': modulos_menu(request),
            'menu_activo': 'metricas_criterios_benchmark',
            'seccion_titulo': '3.1 Criterios de Benchmark (Google y ClientBeat)',
            'config': config,
            'filtro_temporal': config.bm_filtro_temporal_default,
            'filtro_geografico': config.bm_filtro_geografico_default,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        config = ConfiguracionMetricas.get_solo()
        config.bm_min_empresas = int(request.POST.get('bm_min_empresas', 3))
        config.bm_min_valoraciones = int(request.POST.get('bm_min_valoraciones', 10))
        config.bm_dias_sin_valoraciones_excluir = int(request.POST.get('bm_dias_sin_valoraciones_excluir', 90))
        config.bm_filtro_temporal_default = request.POST.get('bm_filtro_temporal_default', 'MENSUAL')
        config.bm_filtro_geografico_default = request.POST.get('bm_filtro_geografico_default', 'COMUNAL')
        config.bm_criterio_desempate = request.POST.get('bm_criterio_desempate', 'DECIMAS')
        config.bm_nota_explicativa_usuario = request.POST.get('bm_nota_explicativa_usuario', '')
        config.save()
        _auditar(request, AccionAuditoriaChoices.EDITAR, ModuloAuditoriaChoices.BENCHMARK, config, descripcion='Actualizó criterios de Benchmark')
        messages.success(request, 'Criterios de Benchmark actualizados correctamente.')
        return redirect('adminpanel:metricas_criterios_benchmark')


class MetricasCsatNpsView(AdminSoporteRequiredMixin, View):
    """3.2 CSAT y NPS: Criterios metodológicos y cálculo."""
    template_name = 'admin_panel/metricas/csat_nps.html'

    def get(self, request):
        config = ConfiguracionMetricas.get_solo()
        context = {
            'menu': modulos_menu(request),
            'menu_activo': 'metricas_csat_nps',
            'seccion_titulo': '3.2 Criterios de Métricas CSAT y NPS',
            'config': config,
            'filtro_temporal': config.csat_nps_filtro_temporal_default,
            'filtro_geografico': config.csat_nps_filtro_geografico_default,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        config = ConfiguracionMetricas.get_solo()
        config.csat_nps_criterio_metodologico = request.POST.get('csat_nps_criterio_metodologico', '')
        config.csat_nps_min_empresas_benchmark = int(request.POST.get('csat_nps_min_empresas_benchmark', 3))
        config.csat_nps_min_valoraciones = int(request.POST.get('csat_nps_min_valoraciones', 5))
        config.csat_nps_dias_sin_valoraciones_excluir = int(request.POST.get('csat_nps_dias_sin_valoraciones_excluir', 60))
        config.csat_nps_filtro_temporal_default = request.POST.get('csat_nps_filtro_temporal_default', 'MENSUAL')
        config.csat_nps_filtro_geografico_default = request.POST.get('csat_nps_filtro_geografico_default', 'COMUNAL')
        config.csat_nps_criterio_desempate = request.POST.get('csat_nps_criterio_desempate', 'DECIMAS')
        config.save()
        _auditar(request, AccionAuditoriaChoices.EDITAR, ModuloAuditoriaChoices.OTRO, config, descripcion='Actualizó criterios CSAT/NPS')
        messages.success(request, 'Criterios de CSAT y NPS actualizados correctamente.')
        return redirect('adminpanel:metricas_csat_nps')


class MetricasResenasGoogleView(AdminSoporteRequiredMixin, View):
    """3.3 Reseñas Google: parámetros y categorías."""
    template_name = 'admin_panel/metricas/resenas_google.html'

    def get(self, request):
        config = ConfiguracionMetricas.get_solo()
        context = {
            'menu': modulos_menu(request),
            'menu_activo': 'metricas_resenas_google',
            'seccion_titulo': '3.3 Criterios de Reseñas Google',
            'config': config,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        config = ConfiguracionMetricas.get_solo()
        config.resenas_minimo_para_analisis = int(request.POST.get('resenas_minimo_para_analisis', 5))
        config.resenas_dias_sin_valoraciones_no_mostrar = int(request.POST.get('resenas_dias_sin_valoraciones_no_mostrar', 120))
        cats_raw = request.POST.get('resenas_categorias_agrupacion', '')
        if cats_raw:
            config.resenas_categorias_agrupacion = [c.strip() for c in cats_raw.split(',') if c.strip()]
        config.save()
        _auditar(request, AccionAuditoriaChoices.EDITAR, ModuloAuditoriaChoices.RESEÑAS_GOOGLE, config, descripcion='Actualizó parámetros de Reseñas Google')
        messages.success(request, 'Parámetros de Reseñas Google actualizados correctamente.')
        return redirect('adminpanel:metricas_resenas_google')


# ==============================
# 4. PLANES VIEWS
# ==============================
class PlanesEditarView(AdminSoporteRequiredMixin, ListView):
    """4.1 Editar Planes (Precios, características, agregar/eliminar, activar/desactivar)."""
    template_name = 'admin_panel/planes/editar.html'
    context_object_name = 'planes'

    def get_queryset(self):
        return Plan.objects.all().order_by('orden', 'precio_clp')


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'planes_editar'
        ctx['seccion_titulo'] = '4.1 Editar y Gestionar Planes de Servicio'
        return ctx


class AdminPanelPlanDeleteView(AdminSoporteRequiredMixin, View):
    """Eliminar un plan de servicio."""
    def post(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        nombre = plan.nombre
        plan.delete()
        _auditar(request, AccionAuditoriaChoices.ELIMINAR, ModuloAuditoriaChoices.PLANES, plan, descripcion=f'Eliminó plan {nombre}')
        messages.success(request, f'El plan "{nombre}" fue eliminado correctamente.')
        return redirect('adminpanel:planes_editar')


# ==============================
# 5. RECURSOS VIEWS
# ==============================
class RecursosDocumentosView(AdminSoporteRequiredMixin, TemplateView):
    """5.1 Cargar o bajar documentos (Fase 2)."""
    template_name = 'admin_panel/recursos/documentos.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'recursos_documentos'
        ctx['seccion_titulo'] = '5.1 Gestión de Documentos (Fase 2)'
        return ctx


class RecursosNoticiasView(AdminSoporteRequiredMixin, TemplateView):
    """5.2 Noticias (Fase 2)."""
    template_name = 'admin_panel/recursos/noticias.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'recursos_noticias'
        ctx['seccion_titulo'] = '5.2 Publicación de Noticias (Fase 2)'
        return ctx


class RecursosReconocimientoView(AdminSoporteRequiredMixin, TemplateView):
    """5.3 Reconocimiento (Fase 1 / Programa de Distinción de Negocios)."""
    template_name = 'admin_panel/recursos/reconocimiento.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'recursos_reconocimiento'
        ctx['seccion_titulo'] = '5.3 Programa de Reconocimiento y Sellos'
        return ctx


# ==============================
# 6. NOTIFICACIONES VIEWS
# ==============================
class NotificacionesEditarEmitirView(AdminSoporteRequiredMixin, View):
    """6.1 Editar y emitir notificaciones a clientes/usuarios."""
    template_name = 'admin_panel/notificaciones/index.html'

    def get(self, request):
        from apps.notifications.models import PlantillaNotificacion, Notificacion
        context = {
            'menu': modulos_menu(request),
            'menu_activo': 'notificaciones',
            'seccion_titulo': '6.1 Editar y Emitir Notificaciones',
            'plantillas': PlantillaNotificacion.objects.all(),
            'notificaciones_recientes': Notificacion.objects.select_related('usuario', 'negocio').order_by('-fecha_creacion')[:30],
            'planes': Plan.objects.filter(activo=True),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        tipo = request.POST.get('tipo', 'INFO')
        canal = request.POST.get('canal', 'IN_APP')
        target_plan = request.POST.get('target_plan')

        from apps.notifications.models import Notificacion
        negocios = Negocio.objects.filter(estado='ACTIVO')
        if target_plan:
            negocios = negocios.filter(suscripcion__plan_id=target_plan)

        count = 0
        for neg in negocios:
            if neg.dueño:
                Notificacion.objects.create(
                    usuario=neg.dueño,
                    negocio=neg,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo=tipo,
                    canal=canal,
                )
                count += 1

        _auditar(request, AccionAuditoriaChoices.CREAR, ModuloAuditoriaChoices.PLANTILLAS_NOTIFICACIONES, None, descripcion=f'Emitió notificación masiva a {count} usuarios')
        messages.success(request, f'Notificación emitida con éxito a {count} usuarios de la plataforma.')
        return redirect('adminpanel:notificaciones')


# ==============================
# PERFIL & PREVIEW VIEWS
# ==============================
class AdminPerfilView(AdminSoporteRequiredMixin, View):
    """Gestión de perfil e información personal del Administrador."""
    template_name = 'admin_panel/perfil.html'

    def get(self, request):
        context = {
            'menu': modulos_menu(request),
            'menu_activo': 'perfil',
            'seccion_titulo': 'Mi Perfil de Administrador',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        password_actual = request.POST.get('password_actual')
        nueva_password = request.POST.get('nueva_password')

        user.first_name = first_name
        user.last_name = last_name
        user.telefono = telefono

        if nueva_password:
            if not password_actual or not user.check_password(password_actual):
                messages.error(request, 'La contraseña actual ingresada es incorrecta.')
                return redirect('adminpanel:perfil')
            user.set_password(nueva_password)
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, '¡Contraseña actualizada con éxito!')

        user.save()
        _auditar(request, AccionAuditoriaChoices.EDITAR, ModuloAuditoriaChoices.USUARIOS, user, descripcion='Actualizó su perfil de administrador')
        messages.success(request, 'Información de perfil actualizada correctamente.')
        return redirect('adminpanel:perfil')


class AdminPreviewClienteView(AdminSoporteRequiredMixin, View):
    """Modo Vista Previa de Cliente para el Administrador de Servicios."""
    def get(self, request):
        request.session['admin_preview_modo'] = True
        messages.info(request, 'Modo Vista Previa activado. Visualizando el dashboard como cliente.')
        return redirect('/dashboard/?admin_preview=1')


class AdminPanelPlanMarcarDefaultView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        with transaction.atomic():
            Plan.objects.all().update(es_plan_default=False)
            plan.es_plan_default = True
            plan.save()
        _auditar(request, AccionAuditoriaChoices.MARCAR_DEFAULT, ModuloAuditoriaChoices.PLANES, plan, descripcion=f'Marcar plan default {plan.nombre}')
        messages.success(request, f'Ahora el plan default es "{plan.nombre}".')
        return redirect('adminpanel:planes_editar')


class AdminPanelSuscripcionCreateView(AdminSoporteRequiredMixin, View):
    def get(self, request):
        negocio_id = request.GET.get('negocio_id')
        context = {
            'menu': modulos_menu(request),
            'menu_activo': 'suscripciones',
            'seccion_titulo': 'Asignar Nueva Suscripción',
            'negocios': Negocio.objects.filter(estado='ACTIVO'),
            'planes': Plan.objects.filter(activo=True),
            'negocio_seleccionado': get_object_or_404(Negocio, pk=negocio_id) if negocio_id else None,
        }
        return render(request, 'admin_panel/suscripcion_nueva.html', context)

    def post(self, request):
        negocio_id = request.POST.get('negocio_id')
        plan_id = request.POST.get('plan_id')
        dias = int(request.POST.get('dias', 30))
        negocio = get_object_or_404(Negocio, pk=negocio_id)
        plan = get_object_or_404(Plan, pk=plan_id)

        negocio.suscripciones.filter(estado=EstadoSuscripcionChoices.ACTIVA).update(estado=EstadoSuscripcionChoices.CANCELADA, cancelada_en=timezone.now())

        nueva_sus = Suscripcion.objects.create(
            negocio=negocio,
            plan=plan,
            estado=EstadoSuscripcionChoices.ACTIVA,
            fecha_inicio=timezone.now(),
            fecha_vencimiento=timezone.now() + timezone.timedelta(days=dias),
        )
        _auditar(request, AccionAuditoriaChoices.CREAR, ModuloAuditoriaChoices.SUSCRIPCIONES, nueva_sus, descripcion=f'Asignó plan {plan.nombre} a {negocio.nombre}')
        messages.success(request, f'Suscripción al plan "{plan.nombre}" asignada correctamente a {negocio.nombre}.')
        return redirect('adminpanel:negocio_detalle', pk=negocio.id)



