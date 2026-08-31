from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # ==============================
    # DASHBOARD PRINCIPAL & PERFIL
    # ==============================
    path('', views.AdminPanelDashboardView.as_view(), name='dashboard'),
    path('perfil/', views.AdminPerfilView.as_view(), name='perfil'),
    path('preview-cliente/', views.AdminPreviewClienteView.as_view(), name='preview_cliente'),

    # ==============================
    # 1. REPORTERÍA
    # ==============================
    path('reporteria/clientes/', views.ReporteriaClientesView.as_view(), name='reporteria_clientes'),
    path('reporteria/benchmark-rubro/', views.ReporteriaBenchmarkRubroView.as_view(), name='reporteria_benchmark_rubro'),
    path('reporteria/tendencias-resenas/', views.ReporteriaTendenciasResenasView.as_view(), name='reporteria_tendencias_resenas'),
    path('reporteria/planes/', views.ReporteriaPlanesView.as_view(), name='reporteria_planes'),

    # ==============================
    # 2. DATA GOOGLE
    # ==============================
    path('data-google/rubros/', views.DataGoogleRubrosView.as_view(), name='datagoogle_rubros'),

    # ==============================
    # 3. MÉTRICAS
    # ==============================
    path('metricas/criterios-benchmark/', views.MetricasCriteriosBenchmarkView.as_view(), name='metricas_criterios_benchmark'),
    path('metricas/csat-nps/', views.MetricasCsatNpsView.as_view(), name='metricas_csat_nps'),
    path('metricas/resenas-google/', views.MetricasResenasGoogleView.as_view(), name='metricas_resenas_google'),

    # ==============================
    # 4. PLANES
    # ==============================
    path('planes/editar/', views.PlanesEditarView.as_view(), name='planes_editar'),
    path('planes/crear/', views.AdminPanelPlanCreateView.as_view(), name='plan_create'),
    path('planes/<uuid:pk>/editar/', views.AdminPanelPlanUpdateView.as_view(), name='plan_update'),
    path('planes/<uuid:pk>/toggle-activo/', views.AdminPanelPlanToggleActivoView.as_view(), name='plan_toggle_activo'),
    path('planes/<uuid:pk>/marcar-default/', views.AdminPanelPlanMarcarDefaultView.as_view(), name='plan_marcar_default'),
    path('planes/<uuid:pk>/eliminar/', views.AdminPanelPlanDeleteView.as_view(), name='plan_delete'),


    # ==============================
    # 5. RECURSOS
    # ==============================
    path('recursos/reconocimiento/', views.RecursosReconocimientoView.as_view(), name='recursos_reconocimiento'),

    # ==============================
    # 6. NOTIFICACIONES
    # ==============================
    path('notificaciones/', views.NotificacionesEditarEmitirView.as_view(), name='notificaciones'),
    path('notificaciones/<int:pk>/toggle-activa/', views.AdminPanelPlantillaNotifToggleActivaView.as_view(), name='plantilla_notif_toggle_activa'),

    # ==============================
    # RUTAS AUXILIARES / SUB-FLUJOS Y ALIAS RETROCOMPATIBLES
    # ==============================
    path('clientes/', views.ReporteriaClientesView.as_view(), name='negocios'),
    path('clientes/<uuid:pk>/', views.AdminPanelNegocioDetailView.as_view(), name='negocio_detalle'),
    path('clientes/<uuid:pk>/cambiar-estado/', views.AdminPanelNegocioCambiarEstadoView.as_view(), name='negocio_cambiar_estado'),
    path('clientes/<uuid:pk>/reiniciar-onboarding/', views.AdminPanelNegocioReiniciarOnboardingView.as_view(), name='negocio_reiniciar_onboarding'),
    path('clientes/<uuid:pk>/reasignar-dueno/', views.AdminPanelNegocioReasignarDuenoView.as_view(), name='negocio_reasignar_dueno'),

    path('suscripciones/', views.ReporteriaPlanesView.as_view(), name='suscripciones'),
    path('suscripciones/nueva/', views.AdminPanelSuscripcionCreateView.as_view(), name='suscripcion_nueva'),
    path('suscripciones/<uuid:pk>/', views.AdminPanelSuscripcionDetailView.as_view(), name='suscripcion_detalle'),
    path('suscripciones/<uuid:pk>/confirmar/', views.AdminPanelSuscripcionConfirmarView.as_view(), name='suscripcion_confirmar'),
    path('suscripciones/<uuid:pk>/cancelar/', views.AdminPanelSuscripcionCancelarView.as_view(), name='suscripcion_cancelar'),
    path('suscripciones/<uuid:pk>/extender/', views.AdminPanelSuscripcionExtenderView.as_view(), name='suscripcion_extender'),
    path('suscripciones/<uuid:pk>/cambiar-plan/', views.AdminPanelSuscripcionCambiarPlanView.as_view(), name='suscripcion_cambiar_plan'),

    path('usuarios/', views.AdminPanelUsuariosListView.as_view(), name='usuarios'),
    path('usuarios/<uuid:pk>/cambiar-rol/', views.AdminPanelUsuarioCambiarRolView.as_view(), name='usuario_cambiar_rol'),
    path('usuarios/<uuid:pk>/cambiar-estado/', views.AdminPanelUsuarioCambiarEstadoView.as_view(), name='usuario_cambiar_estado'),
    path('usuarios/<uuid:pk>/reset-clave/', views.AdminPanelUsuarioResetClaveView.as_view(), name='usuario_reset_clave'),


    path('pagos/', views.AdminPanelAuditoriaListView.as_view(), name='pagos'),
    path('planes/', views.PlanesEditarView.as_view(), name='planes'),
    path('rubros/', views.DataGoogleRubrosView.as_view(), name='rubros'),
    path('plantillas/', views.AdminPanelPlantillasListView.as_view(), name='plantillas'),
    path('plantillas/<int:pk>/toggle-activa/', views.AdminPanelPlantillaToggleActivaView.as_view(), name='plantilla_toggle_activa'),
    path('plantillas/<int:pk>/marcar-default/', views.AdminPanelPlantillaMarcarDefaultView.as_view(), name='plantilla_marcar_default'),
    path('plantillas-notificaciones/', views.AdminPanelPlantillasNotifListView.as_view(), name='plantillas_notificaciones'),
    path('metodologia/', views.AdminPanelMetodologiaView.as_view(), name='metodologia'),

    path('rubros/<int:pk>/toggle-activo/', views.AdminPanelRubroToggleActivoView.as_view(), name='rubro_toggle_activo'),
    path('auditoria/', views.AdminPanelAuditoriaListView.as_view(), name='auditoria'),
]
