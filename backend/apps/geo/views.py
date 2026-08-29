from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from .models import Region, Provincia, Comuna


@require_GET
def api_provincias_por_region(request, region_id):
    region = get_object_or_404(Region, id=region_id, activo=True)
    provincias = (
        Provincia.objects
        .filter(region=region)
        .order_by('orden', 'nombre')
        .values('id', 'nombre')
    )
    return JsonResponse({'ok': True, 'provincias': list(provincias), 'region_nombre': str(region)})


@require_GET
def api_comunas_por_provincia(request, provincia_id):
    provincia = get_object_or_404(Provincia, id=provincia_id)
    comunas = (
        Comuna.objects
        .filter(provincia=provincia)
        .order_by('orden', 'nombre')
        .values('id', 'nombre')
    )
    return JsonResponse({
        'ok': True,
        'comunas': list(comunas),
        'provincia_nombre': provincia.nombre,
        'region_id': provincia.region_id,
    })
