from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('flow/iniciar/', views.IniciarPagoFlowView.as_view(), name='flow_iniciar'),
    path('flow/retorno/', views.RetornoPagoFlowView.as_view(), name='flow_retorno'),
    path('flow/webhook/', views.WebhookPagoFlowView.as_view(), name='flow_webhook'),
]
