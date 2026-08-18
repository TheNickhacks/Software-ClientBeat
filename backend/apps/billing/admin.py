from django.contrib import admin
from django.db.models import Q
from django.contrib import messages
from apps.accounts.admin_mixins import SuperUserOnlyAdminMixin
from .models import Plan, Suscripcion, Pago, RegistroCobranza


@admin.register(Plan)
class PlanAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        'orden',
        'nombre',
        'nombre_mostrar',
        'get_precio_display_admin',
        'locales_permitidos',
        'costo_local_adicional_clp',
        'rubros_permitidos',
        'costo_rubro_adicional_clp',
        'usuarios_permitidos',
        'tiene_benchmarking_rubro',
        'tiene_encuestas_custom',
        'max_preguntas_encuesta_custom',
        'dias_prueba_gratis',
        'es_plan_default',
        'es_lanzamiento_gratis',
        'activo',
        'fecha_creacion',
    ]
    list_display_links = ['nombre', 'nombre_mostrar']
    list_filter = [
        'activo',
        'moneda',
        'es_plan_default',
        'es_lanzamiento_gratis',
        'tiene_benchmarking_rubro',
        'tiene_encuestas_custom',
    ]
    search_fields = ['nombre', 'nombre_mostrar', 'descripcion', 'caracteristicas']
    readonly_fields = ['id', 'fecha_creacion']
    ordering = ['orden', '-fecha_creacion']
    list_editable = ['orden', 'es_plan_default', 'activo']
    filter_horizontal = ['rubros']
    actions = [
        'marcar_como_default',
        'desmarcar_default_todos',
        'activar_planes',
        'desactivar_planes',
    ]
    fieldsets = (
        (None, {
            'fields': (
                'id',
                'nombre',
                'nombre_mostrar',
                'descripcion',
                'caracteristicas',
                'orden',
                'es_plan_default',
                'es_lanzamiento_gratis',
                'activo',
            )
        }),
        ('Precios base y límites', {
            'fields': (
                'moneda',
                'precio_clp',
                'precio_uf',
                'locales_permitidos',
                'usuarios_permitidos',
                'rubros_permitidos',
                'dias_prueba_gratis',
            )
        }),
        ('Cobros extra escalonados (Doc: desde 4° local / 4° rubro online cobran extra)', {
            'fields': (
                ('locales_gratis_incluidos', 'costo_local_adicional_clp'),
                ('rubros_gratis_incluidos', 'costo_rubro_adicional_clp'),
                'rubros',
            ),
        }),
        ('Feature flags - 3 niveles funcionales Plan (Doc Descripcion App)', {
            'fields': (
                ('tiene_benchmarking_rubro',),
                ('tiene_encuestas_custom', 'max_preguntas_encuesta_custom'),
            ),
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',),
        }),
    )

    def get_precio_display_admin(self, obj):
        return obj.get_precio_display()
    get_precio_display_admin.short_description = 'Precio'
    get_precio_display_admin.admin_order_field = 'precio_clp'

    def save_model(self, request, obj, form, change):
        if obj.es_plan_default:
            Plan.objects.filter(
                ~Q(id=obj.id) if obj.id else Q()
            ).update(es_plan_default=False)
        super().save_model(request, obj, form, change)

    @admin.action(description='Marcar seleccionados como Plan por Defecto (onboarding)')
    def marcar_como_default(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                'Selecciona solo UN plan para marcar como por defecto.',
                level=messages.ERROR,
            )
            return
        plan = queryset.first()
        if not plan.activo:
            self.message_user(
                request,
                'No se puede marcar como default un plan inactivo.',
                level=messages.ERROR,
            )
            return
        Plan.objects.all().update(es_plan_default=False)
        plan.es_plan_default = True
        plan.save(update_fields=['es_plan_default'])
        self.message_user(
            request,
            f'✅ Plan "{plan.get_nombre_mostrar()}" ahora es el Plan por Defecto para el onboarding.',
            level=messages.SUCCESS,
        )

    @admin.action(description='Desmarcar todos como Plan por Defecto')
    def desmarcar_default_todos(self, request, queryset):
        actualizados = Plan.objects.filter(es_plan_default=True).update(es_plan_default=False)
        self.message_user(
            request,
            f'ℹ️ Se desmarcaron {actualizados} plan(es) como por defecto. Asegúrate de marcar uno nuevo antes de nuevos onboardings.',
            level=messages.WARNING,
        )

    @admin.action(description='Activar planes seleccionados')
    def activar_planes(self, request, queryset):
        n = queryset.update(activo=True)
        self.message_user(request, f'✅ {n} plan(es) activados correctamente.')

    @admin.action(description='Desactivar planes seleccionados')
    def desactivar_planes(self, request, queryset):
        n = queryset.update(activo=False)
        self.message_user(request, f'⚠️ {n} plan(es) desactivados. No afecta suscripciones ya activas.')


@admin.register(Suscripcion)
class SuscripcionAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'negocio', 'plan', 'estado', 'fecha_inicio', 'fecha_vencimiento', 'renovacion_automatica']
    list_filter = ['estado', 'renovacion_automatica', 'plan']
    search_fields = ['negocio__nombre', 'motivo_cancelacion']
    readonly_fields = ['id']
    raw_id_fields = ['negocio', 'plan']


@admin.register(Pago)
class PagoAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['flow_order_id', 'suscripcion', 'monto', 'moneda', 'estado', 'fecha_pago', 'firma_validada', 'fecha_creacion']
    list_filter = ['estado', 'moneda', 'firma_validada']
    search_fields = ['flow_order_id', 'suscripcion__id']
    readonly_fields = ['id', 'fecha_creacion']
    raw_id_fields = ['suscripcion']


@admin.register(RegistroCobranza)
class RegistroCobranzaAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'suscripcion', 'tipo', 'enviado', 'fecha_envio', 'destinatario', 'asunto']
    list_filter = ['tipo', 'enviado']
    search_fields = ['destinatario', 'asunto']
    readonly_fields = ['id']
    raw_id_fields = ['suscripcion']
