from django.core.management.base import BaseCommand
from apps.billing.models import Plan


class Command(BaseCommand):
    help = 'Crea o actualiza únicamente los 3 planes oficiales basados en los precios oficializados'

    def handle(self, *args, **kwargs):
        # 1. Desactivar todos los planes antiguos para dejar únicamente los 3 oficiales
        Plan.objects.exclude(nombre__in=['BASICO', 'EMPRESARIAL', 'PROFESIONAL']).update(activo=False, es_plan_default=False)

        # 2. Plan Básico ($50.000, 1 local incluido, $10.000 local adicional)
        plan_basico, created_b = Plan.objects.get_or_create(
            nombre='BASICO',
            defaults={
                'nombre_mostrar': 'Plan Básico',
                'descripcion': 'Ideal para medir la satisfacción de clientes mediante encuestas QR y monitorear reseñas.',
                'precio_clp': 50000,
                'moneda': 'CLP',
                'locales_gratis_incluidos': 1,
                'costo_local_adicional_clp': 10000,
                'locales_permitidos': 100,
                'usuarios_permitidos': 2,
                'tiene_qr_clientbeat': True,
                'tiene_analisis_google': True,
                'tiene_benchmark_clientbeat': False,
                'caracteristicas': [
                    "📲 Encuestas QR ilimitadas con NPS & CSAT",
                    "📊 Métricas CSAT & NPS (ClientBeat)",
                    "⭐ Análisis Reseñas Google",
                    "🏢 1 local incluido ($10.000/mes por local adicional + IVA)",
                    "🔒 Benchmark Google (Próximamente)",
                ],
                'es_lanzamiento_gratis': False,
                'dias_prueba_gratis': 365,
                'es_plan_default': False,
                'orden': 1,
                'activo': True,
                'disponible_para_venta': True,
            }
        )
        if not created_b:
            plan_basico.nombre_mostrar = 'Plan Básico'
            plan_basico.descripcion = 'Ideal para medir la satisfacción de clientes mediante encuestas QR y monitorear reseñas.'
            plan_basico.precio_clp = 50000
            plan_basico.locales_gratis_incluidos = 1
            plan_basico.costo_local_adicional_clp = 10000
            plan_basico.locales_permitidos = 100
            plan_basico.usuarios_permitidos = 2
            plan_basico.tiene_qr_clientbeat = True
            plan_basico.tiene_analisis_google = True
            plan_basico.tiene_benchmark_clientbeat = False
            plan_basico.caracteristicas = [
                "📲 Encuestas QR ilimitadas con NPS & CSAT",
                "📊 Métricas CSAT & NPS (ClientBeat)",
                "⭐ Análisis Reseñas Google",
                "🏢 1 local incluido ($10.000/mes por local adicional + IVA)",
                "🔒 Benchmark Google (Próximamente)",
            ]
            plan_basico.es_plan_default = False
            plan_basico.orden = 1
            plan_basico.activo = True
            plan_basico.disponible_para_venta = True
            plan_basico.save()

        # 3. Plan Empresarial ($70.000, 5 locales incluidos, $8.000 local adicional) - Default
        plan_emp, created_e = Plan.objects.get_or_create(
            nombre='EMPRESARIAL',
            defaults={
                'nombre_mostrar': 'Plan Empresarial',
                'descripcion': 'Para cadenas de locales que buscan análisis multi-sucursal y encuestas QR ilimitadas.',
                'precio_clp': 70000,
                'moneda': 'CLP',
                'locales_gratis_incluidos': 5,
                'costo_local_adicional_clp': 8000,
                'locales_permitidos': 100,
                'usuarios_permitidos': 5,
                'tiene_qr_clientbeat': True,
                'tiene_analisis_google': True,
                'tiene_benchmark_clientbeat': False,
                'caracteristicas': [
                    "📲 Encuestas QR ilimitadas con NPS & CSAT",
                    "📊 Métricas CSAT & NPS (ClientBeat)",
                    "⭐ Análisis Reseñas Google",
                    "🏢 5 locales incluidos ($8.000/mes por local adicional + IVA)",
                    "🔒 Benchmark Google (Próximamente)",
                ],
                'es_lanzamiento_gratis': False,
                'dias_prueba_gratis': 365,
                'es_plan_default': True,
                'orden': 2,
                'activo': True,
                'disponible_para_venta': True,
            }
        )
        if not created_e:
            plan_emp.nombre_mostrar = 'Plan Empresarial'
            plan_emp.descripcion = 'Para cadenas de locales que buscan análisis multi-sucursal y encuestas QR ilimitadas.'
            plan_emp.precio_clp = 70000
            plan_emp.locales_gratis_incluidos = 5
            plan_emp.costo_local_adicional_clp = 8000
            plan_emp.locales_permitidos = 100
            plan_emp.usuarios_permitidos = 5
            plan_emp.tiene_qr_clientbeat = True
            plan_emp.tiene_analisis_google = True
            plan_emp.tiene_benchmark_clientbeat = False
            plan_emp.caracteristicas = [
                "📲 Encuestas QR ilimitadas con NPS & CSAT",
                "📊 Métricas CSAT & NPS (ClientBeat)",
                "⭐ Análisis Reseñas Google",
                "🏢 5 locales incluidos ($8.000/mes por local adicional + IVA)",
                "🔒 Benchmark Google (Próximamente)",
            ]
            plan_emp.es_plan_default = True
            plan_emp.orden = 2
            plan_emp.activo = True
            plan_emp.disponible_para_venta = True
            plan_emp.save()

        # 4. Plan Profesional ($120.000, 10 locales incluidos, $5.000 local adicional) - AÚN NO DISPONIBLE A LA VENTA
        plan_pro, created_p = Plan.objects.get_or_create(
            nombre='PROFESIONAL',
            defaults={
                'nombre_mostrar': 'Plan Profesional',
                'descripcion': 'La solución corporativa completa con Encuestas QR NPS/CSAT y Benchmark ClientBeat por rubro.',
                'precio_clp': 120000,
                'moneda': 'CLP',
                'locales_gratis_incluidos': 10,
                'costo_local_adicional_clp': 5000,
                'locales_permitidos': 100,
                'usuarios_permitidos': 15,
                'tiene_qr_clientbeat': True,
                'tiene_analisis_google': True,
                'tiene_benchmark_clientbeat': True,
                'caracteristicas': [
                    "📲 Encuestas QR ilimitadas con NPS & CSAT",
                    "📊 Métricas CSAT & NPS (ClientBeat)",
                    "⭐ Análisis Reseñas Google",
                    "🏢 10 locales incluidos ($5.000/mes por local adicional + IVA)",
                    "🏆 Benchmark ClientBeat por Rubro",
                    "🔒 Benchmark Google (Próximamente)",
                ],
                'es_lanzamiento_gratis': False,
                'dias_prueba_gratis': 365,
                'es_plan_default': False,
                'orden': 3,
                'activo': True,
                'disponible_para_venta': False,  # <-- CTA AÚN NO DISPONIBLE A LA VENTA
            }
        )
        if not created_p:
            plan_pro.nombre_mostrar = 'Plan Profesional'
            plan_pro.descripcion = 'La solución corporativa completa con Encuestas QR NPS/CSAT y Benchmark ClientBeat por rubro.'
            plan_pro.precio_clp = 120000
            plan_pro.locales_gratis_incluidos = 10
            plan_pro.costo_local_adicional_clp = 5000
            plan_pro.locales_permitidos = 100
            plan_pro.usuarios_permitidos = 15
            plan_pro.tiene_qr_clientbeat = True
            plan_pro.tiene_analisis_google = True
            plan_pro.tiene_benchmark_clientbeat = True
            plan_pro.caracteristicas = [
                "📲 Encuestas QR ilimitadas con NPS & CSAT",
                "📊 Métricas CSAT & NPS (ClientBeat)",
                "⭐ Análisis Reseñas Google",
                "🏢 10 locales incluidos ($5.000/mes por local adicional + IVA)",
                "🏆 Benchmark ClientBeat por Rubro",
                "🔒 Benchmark Google (Próximamente)",
            ]
            plan_pro.es_plan_default = False
            plan_pro.orden = 3
            plan_pro.activo = True
            plan_pro.disponible_para_venta = False
            plan_pro.save()

        self.stdout.write(self.style.SUCCESS("[OK] Se han configurado exitosamente los 3 planes oficiales en el sistema."))
