from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.AdminPanelDashboardView.as_view(), name='dashboard'),
    path('rubros/', views.PlaceholderView.as_view(titulo='Gestión de Rubros', icono='fa-list-ul', color='purple'), name='rubros'),
    path('planes/', views.AdminPanelPlanesListView.as_view(), name='planes'),
    path('planes/crear/', views.AdminPanelPlanCreateView.as_view(), name='plan_create'),
    path('planes/<int:pk>/editar/', views.AdminPanelPlanUpdateView.as_view(), name='plan_update'),
    path('planes/<int:pk>/toggle-activo/', views.AdminPanelPlanToggleActivoView.as_view(), name='plan_toggle_activo'),
    path('planes/<int:pk>/marcar-default/', views.AdminPanelPlanMarcarDefaultView.as_view(), name='plan_marcar_default'),
    path('plantillas/', views.PlaceholderView.as_view(titulo='Plantillas de Encuestas', icono='fa-file-alt', color='indigo'), name='plantillas'),
    path('negocios/', views.PlaceholderView.as_view(titulo='Gestión de Negocios Clientes', icono='fa-store', color='green'), name='negocios'),
    path('usuarios/', views.PlaceholderView.as_view(titulo='Gestión de Usuarios', icono='fa-users-cog', color='orange'), name='usuarios'),
    path('solicitudes-arco/', views.PlaceholderView.as_view(titulo='Solicitudes ARCOPB y Privacidad', icono='fa-shield-alt', color='red'), name='solicitudes_arco'),
    path('superuser/salud/', views.SuperSaludView.as_view(), name='super_salud'),
]
