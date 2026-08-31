from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # ==============================
    # DASHBOARD
    # ==============================
    path('', views.AdminPanelDashboardView.as_view(), name='dashboard'),

    # ==============================
    # SUSCRIPCIONES (7 rutas)
    # ==============================
    path('suscripciones/', views.AdminPanelSuscripcionesListView.as_view(), name='suscripciones'),
    path('suscripciones/<uuid:pk>/', views.AdminPanelSuscripcionDetailView.as_view(), name='suscripcion_detalle'),
    path('suscripciones/<uuid:pk>/confirmar/', views.AdminPanelSuscripcionConfirmarView.as_view(), name='suscripcion_confirmar'),
    path('suscripciones/<uuid:pk>/cancelar/', views.AdminPanelSuscripcionCancelarView.as_view(), name='suscripcion_cancelar'),
    path('suscripciones/<uuid:pk>/extender/', views.AdminPanelSuscripcionExtenderView.as_view(), name='suscripcion_extender'),
    path('suscripciones/<uuid:pk>/cambiar-plan/', views.AdminPanelSuscripcionCambiarPlanView.as_view(), name='suscripcion_cambiar_plan'),
    path('suscripciones/nueva/', views.AdminPanelSuscripcionNuevaView.as_view(), name='suscripcion_nueva'),

    # ==============================
    # PAGOS Y COBRANZA
    # ==============================
    path('pagos/', views.AdminPanelPagosListView.as_view(), name='pagos'),

    # ==============================
    # PLANES (5 rutas + simulador)
    # ==============================
    path('planes/', views.AdminPanelPlanesListView.as_view(), name='planes'),
    path('planes/crear/', views.AdminPanelPlanCreateView.as_view(), name='plan_create'),
    path('planes/<uuid:pk>/editar/', views.AdminPanelPlanUpdateView.as_view(), name='plan_update'),
    path('planes/<uuid:pk>/toggle-activo/', views.AdminPanelPlanToggleActivoView.as_view(), name='plan_toggle_activo'),
    path('planes/<uuid:pk>/marcar-default/', views.AdminPanelPlanMarcarDefaultView.as_view(), name='plan_marcar_default'),
    path('simulador-planes/', views.AdminPanelSimuladorPlanesView.as_view(), name='simulador_planes'),

    # ==============================
    # NEGOCIOS / CLIENTES (5 rutas)
    # ==============================
    path('negocios/', views.AdminPanelNegociosListView.as_view(), name='negocios'),
    path('negocios/<uuid:pk>/', views.AdminPanelNegocioDetailView.as_view(), name='negocio_detalle'),
    path('negocios/<uuid:pk>/cambiar-estado/', views.AdminPanelNegocioCambiarEstadoView.as_view(), name='negocio_cambiar_estado'),
    path('negocios/<uuid:pk>/reiniciar-onboarding/', views.AdminPanelNegocioReiniciarOnboardingView.as_view(), name='negocio_reiniciar_onboarding'),
    path('negocios/<uuid:pk>/reasignar-dueno/', views.AdminPanelNegocioReasignarDuenoView.as_view(), name='negocio_reasignar_dueno'),

    # ==============================
    # USUARIOS PLATAFORMA (4 rutas) — User model usa UUID pk
    # ==============================
    path('usuarios/', views.AdminPanelUsuariosListView.as_view(), name='usuarios'),
    path('usuarios/<uuid:pk>/cambiar-rol/', views.AdminPanelUsuarioCambiarRolView.as_view(), name='usuario_cambiar_rol'),
    path('usuarios/<uuid:pk>/cambiar-estado/', views.AdminPanelUsuarioCambiarEstadoView.as_view(), name='usuario_cambiar_estado'),
    path('usuarios/<uuid:pk>/reset-clave/', views.AdminPanelUsuarioResetClaveView.as_view(), name='usuario_reset_clave'),

    # ==============================
    # PLANTILLAS ENCUESTAS (4 rutas)
    # ==============================
    path('plantillas/', views.AdminPanelPlantillasListView.as_view(), name='plantillas'),
    path('plantillas/<uuid:pk>/toggle-activa/', views.AdminPanelPlantillaToggleActivaView.as_view(), name='plantilla_toggle_activa'),
    path('plantillas/<uuid:pk>/marcar-default/', views.AdminPanelPlantillaMarcarDefaultView.as_view(), name='plantilla_marcar_default'),
    path('plantillas/<uuid:pk>/duplicar/', views.AdminPanelPlantillaDuplicarView.as_view(), name='plantilla_duplicar'),

    # ==============================
    # PLANTILLAS NOTIFICACIONES (2 rutas) — PlantillaNotificacion usa pk INT (autoincremental Django)
    # ==============================
    path('plantillas-notificaciones/', views.AdminPanelPlantillasNotifListView.as_view(), name='plantillas_notificaciones'),
    path('plantillas-notificaciones/<int:pk>/toggle-activa/', views.AdminPanelPlantillaNotifToggleActivaView.as_view(), name='plantilla_notif_toggle_activa'),

    # ==============================
    # RUBROS (2 rutas) — Rubro (geo) usa pk INT (autoincremental Django)
    # ==============================
    path('rubros/', views.AdminPanelRubrosListView.as_view(), name='rubros'),
    path('rubros/<int:pk>/toggle-activo/', views.AdminPanelRubroToggleActivoView.as_view(), name='rubro_toggle_activo'),

    # ==============================
    # METODOLOGÍA CÁLCULOS
    # ==============================
    path('metodologia/', views.AdminPanelMetodologiaView.as_view(), name='metodologia'),

    # ==============================
    # AUDITORÍA ADMIN
    # ==============================
    path('auditoria/', views.AdminPanelAuditoriaListView.as_view(), name='auditoria'),

    # ==============================
    # SOLICITUDES ARCOPB (placeholder)
    # ==============================
    path('solicitudes-arco/', views.PlaceholderView.as_view(titulo='Solicitudes ARCOPB y Privacidad', icono='fa-shield-alt', color='red'), name='solicitudes_arco'),

    # ==============================
    # SUPERUSER SALUD TÉCNICA
    # ==============================
    path('superuser/salud/', views.SuperSaludView.as_view(), name='super_salud'),
]
