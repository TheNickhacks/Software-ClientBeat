from django.urls import path
from . import views

app_name = 'geo'

urlpatterns = [
    path('api/region/<int:region_id>/provincias/', views.api_provincias_por_region, name='api_provincias'),
    path('api/provincia/<int:provincia_id>/comunas/', views.api_comunas_por_provincia, name='api_comunas'),
]
