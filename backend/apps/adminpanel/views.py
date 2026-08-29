from django.views.generic import TemplateView, ListView, CreateView, UpdateView, View
from django.db import connection
from django.db.models import Count
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from .mixins import AdminSoporteRequiredMixin, SuperUserRequiredMixin
from .forms import PlanForm
from apps.billing.models import Plan
from apps.encuestas.models import PlantillaEncuesta


def modulos_menu(request):
    """Devuelve la lista de items del sidebar (usada en dashboard y base)."""
    return [
        {'label': 'Dashboard', 'url': '/admin-panel/', 'icono': 'fa-tachometer-alt', 'color': 'blue'},
        {'label': 'Rubros', 'url': '/admin-panel/rubros/', 'icono': 'fa-list-ul', 'color': 'purple'},
        {'label': 'Planes y Precios', 'url': '/admin-panel/planes/', 'icono': 'fa-tags', 'color': 'blue'},
        {'label': 'Plantillas Encuestas', 'url': '/admin-panel/plantillas/', 'icono': 'fa-file-alt', 'color': 'indigo'},
        {'label': 'Negocios', 'url': '/admin-panel/negocios/', 'icono': 'fa-store', 'color': 'green'},
        {'label': 'Usuarios', 'url': '/admin-panel/usuarios/', 'icono': 'fa-users-cog', 'color': 'orange'},
        {'label': 'Solicitudes ARCOPB', 'url': '/admin-panel/solicitudes-arco/', 'icono': 'fa-shield-alt', 'color': 'red'},
    ]


class AdminPanelDashboardView(AdminSoporteRequiredMixin, TemplateView):
    """Dashboard principal del panel admin no-técnico."""
    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.billing.models import Plan, Suscripcion, EstadoSuscripcionChoices
        from apps.businesses.models import Negocio, Local, MiembroEquipo, RolChoices
        from apps.encuestas.models import RespuestaEncuesta, EmocionCSATChoices
        from apps.geo.models import Rubro
        from apps.notifications.models import PlantillaNotificacion, CategoriaNotificacionChoices
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Avg, Q, IntegerField
        from django.utils import timezone

        User = get_user_model()
        ahora = timezone.now()
        desde_30d = ahora - timezone.timedelta(days=30)

        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Dashboard'

        # ==============================
        # 1) KPI PRINCIPALES (8 cards)
        # ==============================
        negocios_activos = Negocio.objects.filter(estado='ACTIVO').count()
        suscripciones_activas = Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.ACTIVA).count()
        usuarios_activos = User.objects.filter(is_active=True).count()
        planes_activos = Plan.objects.filter(activo=True).count()
        locales_total = Local.objects.count()
        respuestas_30d = RespuestaEncuesta.objects.filter(fecha_respuesta__gte=desde_30d).count()
        plantillas_notif = PlantillaNotificacion.objects.filter(activo=True).count()
        rubros_activos = Rubro.objects.filter(activo=True).count()

        ctx['kpis'] = [
            ('Negocios activos', negocios_activos, 'text-purple-700', 'bg-purple-100', 'fa-store'),
            ('Suscripciones activas', suscripciones_activas, 'text-green-700', 'bg-green-100', 'fa-credit-card'),
            ('Usuarios plataforma', usuarios_activos, 'text-blue-700', 'bg-blue-100', 'fa-users'),
            ('Planes disponibles', planes_activos, 'text-indigo-700', 'bg-indigo-100', 'fa-tags'),
            ('Locales totales', locales_total, 'text-rose-700', 'bg-rose-100', 'fa-location-dot'),
            ('Respuestas últimos 30d', respuestas_30d, 'text-amber-700', 'bg-amber-100', 'fa-chart-simple'),
            ('Plantillas notif activas', plantillas_notif, 'text-cyan-700', 'bg-cyan-100', 'fa-envelope-open-text'),
            ('Rubros activos GEO DB', rubros_activos, 'text-fuchsia-700', 'bg-fuchsia-100', 'fa-list-check'),
        ]

        # ==============================
        # 2) MÉTRICAS DINÁMICAS RUBROS
        # ==============================
        rubros_top = list(
            Rubro.objects.filter(activo=True)
            .annotate(total_negocios=Count('negocios', distinct=True))
            .order_by('-total_negocios')[:10]
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

        # ==============================
        # 3) PLANES VENDIDOS (count por plan)
        # ==============================
        ventas_planes = (
            Suscripcion.objects
            .filter(estado=EstadoSuscripcionChoices.ACTIVA)
            .values('plan__nombre', 'plan__color_clase_css')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        ventas_planes_list = []
        for vp in ventas_planes:
            ventas_planes_list.append({
                'nombre': vp['plan__nombre'] or 'MVP Básico',
                'total': vp['total'],
                'color': vp['plan__color_clase_css'] or 'bg-slate-500',
            })
        ctx['ventas_planes'] = ventas_planes_list
        ctx['ventas_planes_total'] = sum(v['total'] for v in ventas_planes_list) or 1

        # ==============================
        # 4) ROLES EQUIPO DISTRIBUCIÓN
        # ==============================
        roles_dist = []
        rol_choices_map = {c[0]: c[1] for c in RolChoices.choices}
        for rol_key, rol_label in RolChoices.choices:
            cnt = MiembroEquipo.objects.filter(rol=rol_key).count()
            roles_dist.append({
                'label': rol_label,
                'key': rol_key,
                'total': cnt,
            })
        roles_total = sum(r['total'] for r in roles_dist) or 1
        for r in roles_dist:
            r['pct'] = round(100 * r['total'] / roles_total)
        ctx['roles_distribucion'] = sorted(roles_dist, key=lambda x: -x['total'])

        # ==============================
        # 5) NPS PROMEDIO CROSS-NEGOCIOS (últimos 30d)
        # ==============================
        resp_30d_nps = RespuestaEncuesta.objects.filter(
            fecha_respuesta__gte=desde_30d,
            nps_puntaje__isnull=False,
        )
        total_nps_30d = resp_30d_nps.count()
        if total_nps_30d:
            prom_nps = resp_30d_nps.aggregate(prom=Avg('nps_puntaje'))['prom'] or 0
            promotores_30d = resp_30d_nps.filter(nps_puntaje__gte=9).count()
            pasivos_30d = resp_30d_nps.filter(nps_puntaje__in=[7, 8]).count()
            detractores_30d = resp_30d_nps.filter(nps_puntaje__lte=6).count()
            nps_score_plataforma = round(100 * (promotores_30d - detractores_30d) / total_nps_30d)
        else:
            prom_nps = 0
            promotores_30d = pasivos_30d = detractores_30d = 0
            nps_score_plataforma = 0
        ctx['nps_plataforma'] = {
            'score': nps_score_plataforma,
            'promedio': round(prom_nps, 1),
            'total': total_nps_30d,
            'promotores': promotores_30d,
            'pasivos': pasivos_30d,
            'detractores': detractores_30d,
            'badge': 'Promotor' if nps_score_plataforma >= 50 else 'Pasivo' if nps_score_plataforma >= 0 else 'Detractor',
            'color': 'emerald' if nps_score_plataforma >= 50 else 'amber' if nps_score_plataforma >= 0 else 'rose',
        }

        # ==============================
        # 6) CATEGORÍAS NOTIFICACIONES
        # ==============================
        notif_cats = []
        for cat_key, cat_label in CategoriaNotificacionChoices.choices:
            cnt = PlantillaNotificacion.objects.filter(categoria=cat_key, activo=True).count()
            notif_cats.append({'label': cat_label, 'total': cnt})
        ctx['notificaciones_categorias'] = notif_cats

        # ==============================
        # 7) LISTAS COMPLEMENTARIAS
        # ==============================
        ctx['ultimos_negocios'] = (
            Negocio.objects.select_related('dueño')
            .annotate(cant_locales=Count('locales'))
            .order_by('-fecha_creacion')[:5]
        )
        ctx['ultimas_respuestas_plataforma'] = (
            RespuestaEncuesta.objects.select_related('local__negocio', 'plantilla')
            .order_by('-fecha_respuesta')[:10]
        )
        ctx['vencen_7dias'] = (
            Suscripcion.objects.select_related('negocio', 'plan')
            .filter(estado=EstadoSuscripcionChoices.ACTIVA)
            .order_by('fecha_vencimiento')[:5]
        )
        ctx['planes'] = Plan.objects.filter(activo=True).order_by('orden')
        ctx['fecha_hora_generacion'] = timezone.localtime(ahora).strftime('%Y-%m-%d %H:%M:%S')
        return ctx


# =======================
# CRUD PLANES (ADMIN_SOPORTE)
# =======================

class AdminPanelPlanesListView(AdminSoporteRequiredMixin, ListView):
    """Listado de planes con acciones: crear/editar, activar/desactivar, marcar default."""
    template_name = 'admin_panel/planes_list.html'
    model = Plan
    context_object_name = 'planes'
    ordering = ['orden', 'nombre']

    def get_queryset(self):
        return Plan.objects.all().prefetch_related('rubros').order_by('orden', 'nombre')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Planes y Precios'
        ctx['planes_activos'] = Plan.objects.filter(activo=True).count()
        ctx['planes_total'] = Plan.objects.count()
        ctx['default_plan'] = Plan.objects.filter(es_plan_default=True).first()
        return ctx


class AdminPanelPlanCreateView(AdminSoporteRequiredMixin, CreateView):
    template_name = 'admin_panel/planes_form.html'
    model = Plan
    form_class = PlanForm
    success_url = reverse_lazy('adminpanel:planes')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Planes y Precios'
        ctx['modo'] = 'crear'
        return ctx

    def form_valid(self, form):
        plan = form.save(commit=False)
        # Si se marca default, desmarcar el anterior
        if plan.es_plan_default:
            Plan.objects.filter(es_plan_default=True).update(es_plan_default=False)
        plan.save()
        form.save_m2m()  # guardar M2M rubros
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
        ctx['menu_activo'] = 'Planes y Precios'
        ctx['modo'] = 'editar'
        return ctx

    def form_valid(self, form):
        plan = form.save(commit=False)
        if plan.es_plan_default:
            Plan.objects.filter(es_plan_default=True).exclude(pk=plan.pk).update(es_plan_default=False)
        plan.save()
        form.save_m2m()
        messages.success(self.request, f'Plan "{plan.nombre}" actualizado correctamente.')
        return super().form_valid(form)


class AdminPanelPlanToggleActivoView(AdminSoporteRequiredMixin, View):
    """Activa o desactiva un plan (no lo borra). POST por seguridad."""
    def post(self, request, pk, *args, **kwargs):
        from django.db import transaction
        plan = get_object_or_404(Plan, pk=pk)
        if plan.activo and plan.es_plan_default:
            messages.error(request, f'No puedes desactivar el plan default ({plan.nombre}). Marca otro plan como default primero.')
            return redirect('adminpanel:planes')
        with transaction.atomic():
            plan.activo = not plan.activo
            plan.save(update_fields=['activo', 'fecha_actualizacion'])
        estado = 'activado' if plan.activo else 'desactivado'
        messages.success(request, f'Plan "{plan.nombre}" {estado} exitosamente.')
        return redirect('adminpanel:planes')


class AdminPanelPlanMarcarDefaultView(AdminSoporteRequiredMixin, View):
    """Marca este plan como el default del onboarding (desmarca los demás). POST seguro."""
    def post(self, request, pk, *args, **kwargs):
        from django.db import transaction
        plan = get_object_or_404(Plan, pk=pk)
        if not plan.activo:
            messages.error(request, f'No puedes marcar como default un plan inactivo ({plan.nombre}). Actívalo primero.')
            return redirect('adminpanel:planes')
        with transaction.atomic():
            Plan.objects.all().update(es_plan_default=False)
            plan.es_plan_default = True
            plan.save(update_fields=['es_plan_default', 'fecha_actualizacion'])
        messages.success(request, f'Plan "{plan.nombre}" ahora es el plan default de onboarding.')
        return redirect('adminpanel:planes')


class PlaceholderView(AdminSoporteRequiredMixin, TemplateView):
    template_name = 'admin_panel/placeholder.html'
    titulo = 'Módulo en construcción'
    icono = 'fa-cogs'
    color = 'blue'

    def get_titulo(self):
        return self.titulo

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = self.get_titulo()
        ctx['placeholder_titulo'] = self.get_titulo()
        ctx['placeholder_icono'] = self.icono
        ctx['placeholder_color'] = self.color
        ctx['placeholder_descripcion'] = (
            'Este módulo se implementará próximamente con el panel '
            'no-técnico para gestionar su contenido.'
        )
        return ctx


# =======================
# CRUD PLANTILLAS ENCUESTAS (ADMIN_SOPORTE, NO TÉCNICO)
# =======================

class AdminPanelPlantillasListView(AdminSoporteRequiredMixin, ListView):
    template_name = 'admin_panel/plantillas_list.html'
    model = PlantillaEncuesta
    context_object_name = 'plantillas'
    ordering = ['orden', 'nombre']

    def get_queryset(self):
        return (
            PlantillaEncuesta.objects.all()
            .prefetch_related('rubros')
            .annotate(
                total_respuestas=Count('respuestas'),
            )
            .order_by('orden', 'nombre')
        )

    def get_context_data(self, **kwargs):
        from apps.businesses.models import Local
        ctx = super().get_context_data(**kwargs)
        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Plantillas Encuestas'
        ctx['total_plantillas'] = PlantillaEncuesta.objects.count()
        ctx['plantillas_activas'] = PlantillaEncuesta.objects.filter(activa=True).count()
        ctx['default'] = PlantillaEncuesta.objects.filter(es_default=True).first()
        ctx['total_locales'] = Local.objects.filter(estado='ACTIVO').count()
        return ctx


class AdminPanelPlantillaToggleActivaView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        plant = get_object_or_404(PlantillaEncuesta, pk=pk)
        if plant.es_default and plant.activa:
            messages.error(request, 'No puedes desactivar la plantilla default. Marca otra como default primero.')
            return redirect('adminpanel:plantillas')
        plant.activa = not plant.activa
        plant.save(update_fields=['activa', 'fecha_actualizacion'])
        estado = 'activada' if plant.activa else 'desactivada'
        messages.success(request, f'Plantilla "{plant.nombre}" {estado} exitosamente.')
        return redirect('adminpanel:plantillas')


class AdminPanelPlantillaMarcarDefaultView(AdminSoporteRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        from django.db import transaction
        plant = get_object_or_404(PlantillaEncuesta, pk=pk)
        if not plant.activa:
            messages.error(request, 'No puedes marcar como default una plantilla inactiva. Actívala primero.')
            return redirect('adminpanel:plantillas')
        with transaction.atomic():
            PlantillaEncuesta.objects.all().update(es_default=False)
            plant.es_default = True
            plant.save(update_fields=['es_default', 'fecha_actualizacion'])
        messages.success(request, f'Ahora la plantilla default es: "{plant.nombre}"')
        return redirect('adminpanel:plantillas')



class SuperSaludView(SuperUserRequiredMixin, TemplateView):
    """Vista solo para SuperUser: salud de base de datos y parámetros técnicos."""
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
        return ctx
