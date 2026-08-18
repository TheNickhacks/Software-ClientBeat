from django.views.generic import TemplateView, ListView, CreateView, UpdateView, View
from django.db import connection
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from .mixins import AdminSoporteRequiredMixin, SuperUserRequiredMixin
from .forms import PlanForm
from apps.billing.models import Plan


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
        from apps.businesses.models import Negocio
        from django.contrib.auth import get_user_model
        User = get_user_model()

        ctx['menu'] = modulos_menu(self.request)
        ctx['menu_activo'] = 'Dashboard'
        ctx['kpis'] = [
            ('Negocios registrados', Negocio.objects.filter(estado='ACTIVO').count(), 'text-purple-700', 'bg-purple-100'),
            ('Suscripciones activas', Suscripcion.objects.filter(estado=EstadoSuscripcionChoices.ACTIVA).count(), 'text-green-700', 'bg-green-100'),
            ('Usuarios plataforma', User.objects.filter(is_active=True).count(), 'text-blue-700', 'bg-blue-100'),
            ('Planes disponibles', Plan.objects.filter(activo=True).count(), 'text-indigo-700', 'bg-indigo-100'),
        ]
        ctx['ultimos_negocios'] = (
            Negocio.objects.select_related('dueño')
            .order_by('-fecha_creacion')[:5]
        )
        ctx['vencen_7dias'] = (
            Suscripcion.objects.select_related('negocio', 'plan')
            .filter(estado=EstadoSuscripcionChoices.ACTIVA)
            .order_by('fecha_vencimiento')[:5]
        )
        ctx['planes'] = Plan.objects.filter(activo=True).order_by('orden')
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
