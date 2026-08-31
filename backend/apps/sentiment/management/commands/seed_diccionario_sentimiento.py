from django.core.management.base import BaseCommand, CommandError
from apps.sentiment.models import DiccionarioSentimiento


class Command(BaseCommand):
    help = 'Popula DiccionarioSentimiento con palabras base en español para análisis de reseñas.'

    PALABRAS_POSITIVAS = [
        ('excelente', 1.3), ('espectacular', 1.3), ('recomendable', 1.2), ('favorito', 1.2),
        ('maravilloso', 1.3), ('increible', 1.2), ('increíble', 1.2), ('perfecto', 1.3),
        ('amable', 1.1), ('atento', 1.1), ('rápido', 1.0), ('rapido', 1.0), ('limpio', 1.0),
        ('ordenado', 1.0), ('buena', 1.0), ('bueno', 1.0), ('buen', 1.0), ('bien', 0.8),
        ('calidad', 1.0), ('agradable', 1.0), ('sorpresa', 1.0), ('justos', 0.8), ('justo', 0.8),
        ('volveré', 1.0), ('volveria', 1.0), ('volvería', 1.0), ('genial', 1.2), ('fantastico', 1.2),
        ('fantástico', 1.2), ('diez', 1.1), ('10/10', 1.2), ('primera', 0.6), ('productos', 0.4),
        ('atención', 0.5), ('atencion', 0.5), ('experiencia', 0.5), ('café', 0.3), ('cafe', 0.3),
        ('comida', 0.3), ('personal', 0.3), ('siempre', 0.4), ('pasar', 0.3), ('rato', 0.3),
        ('precios', 0.2), ('opción', 0.3), ('opcion', 0.3), ('servicio', 0.4),
    ]

    PALABRAS_NEUTRAS = [
        ('normal', 0.0), ('regular', -0.1), ('algunos', 0.0), ('detalles', 0.0), ('puede', 0.0),
        ('mejorar', -0.1), ('esperaba', -0.2), ('esperaba', -0.2), ('veces', 0.0), ('esperar', -0.1),
        ('poco', -0.2), ('mixto', 0.0), ('mixta', 0.0), ('estuvo', 0.0), ('general', 0.1),
        ('par', 0.0), ('un', 0.0), ('una', 0.0), ('por', 0.0), ('lo', 0.0), ('la', 0.0),
        ('el', 0.0), ('en', 0.0), ('y', 0.0), ('a', 0.0), ('que', 0.0), ('de', 0.0),
    ]

    PALABRAS_NEGATIVAS = [
        ('pésima', -1.3), ('pesima', -1.3), ('pésimo', -1.3), ('pesimo', -1.3),
        ('terrible', -1.3), ('malo', -1.0), ('mala', -1.0), ('mal', -0.9),
        ('no', -0.5), ('jamás', -1.1), ('jamas', -1.1), ('nunca', -1.0),
        ('demoró', -0.9), ('demoro', -0.9), ('lento', -0.8), ('lenta', -0.8), ('demasiado', -0.5),
        ('incompleto', -0.9), ('incompleta', -0.9), ('falta', -0.8), ('faltan', -0.8),
        ('limpieza', -0.7), ('sucio', -1.0), ('desordenado', -0.8), ('reclamar', -0.9),
        ('expectativas', -0.6), ('incumplió', -1.0), ('incumplio', -1.0), ('error', -0.9),
        ('problema', -0.8), ('problemas', -0.9), ('trajeron', -0.7), ('pedí', -0.4), ('pedi', -0.4),
        ('solución', -0.6), ('solucion', -0.6), ('producto', -0.5), ('justita', -0.6),
        ('creo', -0.3), ('pena', -0.4), ('peor', -0.8), ('peores', -0.8),
    ]

    def handle(self, *args, **options):
        from apps.sentiment.models import DiccionarioSentimiento
        creadas = 0
        skip = 0
        categorias = {
            'POSITIVO': (self.PALABRAS_POSITIVAS, 'POSITIVO'),
            'NEUTRO': (self.PALABRAS_NEUTRAS, 'NEUTRO'),
            'NEGATIVO': (self.PALABRAS_NEGATIVAS, 'NEGATIVO'),
        }
        for cat, (lista, polaridad) in categorias.items():
            for palabra, peso in lista:
                palabra_norm = palabra.strip().lower()
                if not palabra_norm:
                    continue
                obj, created = DiccionarioSentimiento.objects.get_or_create(
                    palabra=palabra_norm,
                    defaults={
                        'polaridad': polaridad,
                        'peso': peso,
                        'categoria': 'GENERAL',
                    }
                )
                if created:
                    creadas += 1
                else:
                    skip += 1
        self.stdout.write(self.style.SUCCESS(
            '[DiccionarioSentimiento] Seed OK: creadas=%d, ya_existian=%d, total_actual=%d' % (
                creadas, skip, DiccionarioSentimiento.objects.count()
            )
        ))
