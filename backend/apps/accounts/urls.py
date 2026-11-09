from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.OnboardingWizardView.as_view(), name='register'),
    path('onboarding/', views.OnboardingWizardView.as_view(), name='onboarding'),
    path('perfil/', views.PerfilUsuarioView.as_view(), name='perfil'),
    path('invitacion/<str:token>/', views.AceptarInvitacionView.as_view(), name='aceptar_invitacion'),
    path('password-reset/', views.ClientBeatPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.ClientBeatPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.ClientBeatPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.ClientBeatPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

