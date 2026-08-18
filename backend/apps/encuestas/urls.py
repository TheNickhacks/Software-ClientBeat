from django.urls import path
from . import views

app_name = 'encuestas'

urlpatterns = [
    path('<slug:qr_token>/', views.EncuestaPublicaQRView.as_view(), name='encuesta_publica_qr'),
    path('<slug:qr_token>/gracias/', views.EncuestaGraciasView.as_view(), name='encuesta_gracias'),
]
