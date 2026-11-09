from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Bloqueo estricto por falta de pago (Hard Paywall)
    path('bloqueado/', views.BloqueadoView.as_view(), name='bloqueado'),

    # Flujo de Suscripciones Nativas Flow (Enrolamiento de Tarjeta Oneclick)
    path('flow/suscripcion/iniciar/', views.IniciarSuscripcionFlowView.as_view(), name='flow_suscripcion_iniciar'),
    path('flow/tarjeta-retorno/', views.RetornoRegistroTarjetaFlowView.as_view(), name='flow_tarjeta_retorno'),

    # Flujo Legacy / Directo
    path('flow/iniciar/', views.IniciarPagoFlowView.as_view(), name='flow_iniciar'),
    path('flow/retorno/', views.RetornoPagoFlowView.as_view(), name='flow_retorno'),

    # Webhook Central Flow (Mes 1, Mes 2, fallos y cancelaciones)
    path('flow/webhook/', views.WebhookPagoFlowView.as_view(), name='flow_webhook'),

    # Comprobante / Recibo de Pago Imprimible (PDF)
    path('comprobante/<uuid:pago_id>/', views.ComprobantePagoView.as_view(), name='comprobante_pago'),
]
