from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('legal/<slug:slug>/', views.legal, name='legal'),
]
