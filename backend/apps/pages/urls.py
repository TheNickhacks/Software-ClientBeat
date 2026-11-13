from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/exportar-qr/', views.exportar_matriz_qr_excel, name='exportar_matriz_qr_excel'),
    path('legal/<slug:slug>/', views.legal, name='legal'),
]

