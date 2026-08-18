from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from apps.geo.models import Rubro


class Command(BaseCommand):
    help = (
        'Carga / actualiza Rubros para el dropdown del onboarding del dueño. '
        '40+ rubros típicos Chile (Fuente: alineados con los sectores más medibles en Client Beat: '
        'restaurantes, cafeterías, retail, salud, belleza, educación, automotriz, servicios profesionales, etc.) '
        'Incluye opción "Otro / No está en la lista" con flag es_otro=True. '
        'Usa --reset para limpiar y recargar.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra TODOS los rubros y vuelve a insertar la lista oficial.',
        )

    def handle(self, *args, **options):
        reset = options.get('reset')

        rubros_definicion = [
            # (orden, nombre, tipo, icono, descripcion, es_otro, activo)
            (1, 'Cafeterías, Brunch y Té', 'LOCAL_FISICO', '☕',
             'Cafés, brunch, cafeterías, casas de té, repostería pequeña.', False, True),
            (2, 'Restaurantes y Comidas', 'LOCAL_FISICO', '🍽️',
             'Restaurantes de cocina chilena, internacional, familiar, ejecutiva.', False, True),
            (3, 'Pizzerías', 'LOCAL_FISICO', '🍕', 'Pizzerías al horno, delivery, empanadas pizzetas.', False, True),
            (4, 'Comida Rápida / Fast Food', 'LOCAL_FISICO', '🍔',
             'Hamburgueserías, completos, hot-dogs, sándwiches, pollos a las brasas.', False, True),
            (5, 'Comida Japonesa / Sushi', 'LOCAL_FISICO', '🍣', 'Sushi, makis, ramen, cebicherías japonesas.', False, True),
            (6, 'Comida Peruana / Cevicherías', 'LOCAL_FISICO', '🦐', 'Ceviches, causas, anticuchos, peruanas.', False, True),
            (7, 'Comida Vegetariana / Vegana / Saludable', 'LOCAL_FISICO', '🥗',
             'Comida sana, bowls, ensaladas, juguerías, veganas, vegetarianas.', False, True),
            (8, 'Heladerías, Postres y Repostería', 'LOCAL_FISICO', '🍰',
             'Heladerías, pastelerías, tortas, repostería, galletas, chocolaterías.', False, True),
            (9, 'Panaderías y Pastelerías', 'LOCAL_FISICO', '🥐',
             'Pan, marraqueta, hallulla, pan amasado, panettone, pastelería.', False, True),
            (10, 'Supermercados, Minimarkets y Autoservicio', 'LOCAL_FISICO', '🛒',
             'Supermercados, minimarkets, autoservicio, tiendas de abarrotes.', False, True),
            (11, 'Ferreterías y Materiales de Construcción', 'LOCAL_FISICO', '🔨',
             'Ferreterías, pinturerías, materiales construcción, madereras.', False, True),
            (12, 'Farmacias y Salud Cotidiana', 'LOCAL_FISICO', '💊',
             'Farmacias, sucursales farmacéuticas, perfumerías anexas.', False, True),
            (13, 'Veterinarias, Clínicas Veterinarias y Pet Care', 'LOCAL_FISICO', '🐾',
             'Clínicas veterinarias, veterinarias, atención perros/gatos, pet hospital.', False, True),
            (14, 'Peluquerías, Barberías y Salones', 'LOCAL_FISICO', '✂️',
             'Peluquerías damas/caballeros, barberías, colorimetría, alisados, extensiones.', False, True),
            (15, 'Centros de Estética, Belleza, Uñas y Spa', 'LOCAL_FISICO', '💅',
             'Estéticas, spas, uñas, pestañas, depilación, masajes, faciales.', False, True),
            (16, 'Gimnasios, CrossFit, Box y Fitness', 'LOCAL_FISICO', '🏋️',
             'Gimnasios, crossfit, box functional, yoga, pilates, spinning.', False, True),
            (17, 'Clínicas Médicas y Centros de Salud', 'LOCAL_FISICO', '🏥',
             'Centros médicos, clínicas generales, especialidades, policlínicos.', False, True),
            (18, 'Dentistas y Clínicas Dentales', 'LOCAL_FISICO', '🦷',
             'Dentistas, clínicas dentales, ortodoncia, estética dental, implantes.', False, True),
            (19, 'Ópticas y Salud Visual', 'LOCAL_FISICO', '👓',
             'Ópticas, lentes, oftalmología, exámenes de la vista, lentillas.', False, True),
            (20, 'Hoteles, Moteles, Hostales y Alojamiento', 'LOCAL_FISICO', '🏨',
             'Hoteles, apart-hoteles, hostales, bed & breakfast, moteles.', False, True),
            (21, 'Agencias de Viajes y Turismo', 'AMBOS', '✈️',
             'Agencias de viajes, turismo, tours, paquetes vacacionales, pasajes.', False, True),
            (22, 'Tiendas de Ropa, Moda y Calzado', 'LOCAL_FISICO', '👕',
             'Tiendas de ropa dama/varón/niño, jeans, vestuario, zapatillas.', False, True),
            (23, 'Zapatillas, Zapatos y Accesorios', 'LOCAL_FISICO', '👟',
             'Zapatillas urbanas/running, zapatería, cinturones, carteras.', False, True),
            (24, 'Deportes, Artículos Deportivos y Outdoor', 'LOCAL_FISICO', '🎽',
             'Artículos deportivos, camping, bicicletas, outdoor, natación, ski.', False, True),
            (25, 'Librerías, Papelerías y Escolar', 'LOCAL_FISICO', '📚',
             'Librerías, papelerías, útiles escolares, arte, oficina, cuadernos.', False, True),
            (26, 'Tintorerías y Lavanderías', 'LOCAL_FISICO', '🧺',
             'Lavandería autoservicio, tintorería, lavado de edredones, planchado.', False, True),
            (27, 'Lavado de Autos y Estética Vehicular', 'LOCAL_FISICO', '🧼',
             'Autolavado, lavado de autos, detailing, estéticas vehiculares.', False, True),
            (28, 'Talleres Mecánicos, Automotrices y Servicios Auto', 'LOCAL_FISICO', '🔧',
             'Talleres mecánicos, eléctricos automotrices, suspensiones, neumáticos, servicio técnico.', False, True),
            (29, 'Inmobiliarias y Corretaje de Propiedades', 'AMBOS', '🏠',
             'Inmobiliarias, corredores propiedades, arriendos, ventas casas/deptos.', False, True),
            (30, 'Constructoras y Servicios de Construcción', 'LOCAL_FISICO', '🏗️',
             'Constructoras, remodelaciones, obras civiles, pintura, electricidad, gasfitería.', False, True),
            (31, 'Abogados, Asesorías Legales y Notarías', 'AMBOS', '⚖️',
             'Abogados, asesoría legal, notarías, conservadores, abogado familia/penal/laboral/comercial.', False, True),
            (32, 'Contadores, Auditorías y Asesorías Tributarias', 'AMBOS', '🧾',
             'Contadores, asesoría contable/tributaria, auditorías, boletas/honorarios.', False, True),
            (33, 'Arquitectos, Ingenieros y Servicios Técnicos', 'AMBOS', '📐',
             'Arquitectos, ingenieros civiles/mecánicos/eléctricos, inspecciones, planos.', False, True),
            (34, 'Agencias de Marketing Digital, Publicidad y Diseño', 'AMBOS', '📣',
             'Marketing digital, agencias de publicidad, community management, diseño gráfico/UX.', False, True),
            (35, 'Software, Desarrollo Web, Apps y Tecnología', 'RUBRO_ONLINE', '💻',
             'Desarrollo software, apps, web, SaaS, tech startups, integraciones API.', False, True),
            (36, 'Educación, Cursos, Capacitaciones y Academias', 'AMBOS', '🎓',
             'Cursos, academias idiomas, capacitaciones, formación online, escuelas privadas.', False, True),
            (37, 'Jardines Infantiles, Párvulos y Educación Preescolar', 'LOCAL_FISICO', '🧸',
             'Jardines infantiles, salas cuna, parvularios, guarderías, pre-kinder.', False, True),
            (38, 'Estacionamientos y Garajes', 'LOCAL_FISICO', '🅿️',
             'Estacionamientos públicos/privados, garajes mensuales, valet parking.', False, True),
            (39, 'Eventos, Catering y Gastronomía Eventos', 'AMBOS', '🎉',
             'Empresas de eventos, catering, matrimonios, fiestas empresariales, coffee break.', False, True),
            (40, 'Pet Shop, Tienda de Mascotas y Zoo', 'LOCAL_FISICO', '🐶',
             'Tiendas de mascotas, accesorios perros/gatos, alimentos balanceados, zoo tienda.', False, True),
            (999, 'Otro (No está en la lista)', 'AMBOS', '➕',
             'Usa esta opción si no encuentras tu rubro. El equipo Client Beat se contactará para agregarlo.', True, True),
        ]

        if reset:
            self.stdout.write('[INFO] Reset solicitado: borrando TODOS los rubros existentes...')
            Rubro.objects.all().delete()

        creados = 0
        actualizados = 0
        for orden, nombre, tipo, icono, descripcion, es_otro, activo in rubros_definicion:
            slug = slugify(nombre)
            rubro, created = Rubro.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'slug': slug,
                    'tipo': tipo,
                    'icono': icono,
                    'descripcion': descripcion,
                    'es_otro': es_otro,
                    'orden': orden,
                    'activo': activo,
                }
            )
            if created:
                creados += 1
                continue

            changed = False
            for attr, val in [
                ('slug', slug),
                ('tipo', tipo),
                ('icono', icono),
                ('descripcion', descripcion),
                ('es_otro', es_otro),
                ('orden', orden),
                ('activo', activo),
            ]:
                if getattr(rubro, attr) != val:
                    setattr(rubro, attr, val)
                    changed = True
            if changed:
                rubro.save()
                actualizados += 1

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('   RESULTADO CARGA RUBROS (Onboarding ClienBeat)'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'   Rubros creados:        {creados}')
        self.stdout.write(f'   Rubros actualizados:   {actualizados}')
        self.stdout.write(f'   Rubros totales en BD:  {Rubro.objects.count()}')
        self.stdout.write(f'   Rubros activos:        {Rubro.objects.filter(activo=True).count()}')
        self.stdout.write(f'   Rubros físicos:        {Rubro.objects.filter(tipo="LOCAL_FISICO").count()}')
        self.stdout.write(f'   Rubros online/digital: {Rubro.objects.filter(tipo="RUBRO_ONLINE").count()}')
        self.stdout.write(f'   Rubros mixtos (ambos): {Rubro.objects.filter(tipo="AMBOS").count()}')
        self.stdout.write(f'   Opción "Otro" existe:  {Rubro.objects.filter(es_otro=True).exists()}')
        self.stdout.write(self.style.SUCCESS('=' * 70))
