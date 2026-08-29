from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from apps.geo.models import (
    Rubro, GoogleCategory, RubroDimension, RubroDimensionAtributo,
)


GOOGLE_CATEGORIES_DEF = [
    # (google_en, google_es, has_visible_subratings, subratings_examples, additional_fields, orden)
    ('bakery', 'Panadería', True,
     ['Food & Drink quality', 'Service', 'Atmosphere & Ambience'],
     ['Spend per person ranges (price/value)'], 1),
    ('bar', 'Bar', True,
     ['Food & Drink quality', 'Service', 'Atmosphere & Ambience'],
     ['Spend per person ranges (price/value)'], 2),
    ('beauty_salon', 'Salón de Belleza', True,
     ['Service satisfaction (overall experience)'],
     ['Type of service received', 'Spend per person', 'Style requested'], 3),
    ('book_store', 'Librería', False, [], [], 4),
    ('cafe', 'Cafetería', True,
     ['Food & Drink quality', 'Service', 'Atmosphere & Ambience'],
     ['Spend per person ranges (price/value)'], 5),
    ('car_repair', 'Taller Mecánico', False, [], [], 6),
    ('car_wash', 'Autolavado', False, [], [], 7),
    ('clothing_store', 'Tienda de Ropa', False, [], [], 8),
    ('convenience_store', 'Minimarket / Tienda de Conveniencia', False, [], [], 9),
    ('doctor', 'Consultorio Médico', False, [], [], 10),
    ('electronics_store', 'Tienda de Electrónica', False, [], [], 11),
    ('florist', 'Floristería', False, [], [], 12),
    ('furniture_store', 'Tienda de Muebles', False, [], [], 13),
    ('gym', 'Gimnasio', False, [], [], 14),
    ('hair_care', 'Peluquería', True,
     ['Service satisfaction (overall experience)'],
     ['Type of service received', 'Spend per person', 'Style requested'], 15),
    ('hardware_store', 'Ferretería', False, [], [], 16),
    ('home_goods_store', 'Tienda Artículos Hogar', False, [], [], 17),
    ('jewelry_store', 'Joyería', False, [], [], 18),
    ('laundry', 'Lavandería / Tintorería', False, [], [], 19),
    ('liquor_store', 'Licorería', False, [], [], 20),
    ('meal_delivery', 'Delivery de Comidas', True,
     ['Food & Drink quality', 'Service', 'Atmosphere & Ambience'],
     ['Spend per person ranges (price/value)'], 21),
    ('meal_takeaway', 'Comida para Llevar', True,
     ['Food & Drink quality', 'Service', 'Atmosphere & Ambience'],
     ['Spend per person ranges (price/value)'], 22),
    ('pet_store', 'Tienda de Mascotas', False, [], [], 23),
    ('pharmacy', 'Farmacia', False, [], [], 24),
    ('restaurant', 'Restaurante', True,
     ['Food & Drink quality', 'Service', 'Atmosphere & Ambience'],
     ['Spend per person ranges (price/value)'], 25),
    ('shoe_store', 'Zapatería', False, [], [], 26),
    ('shopping_mall', 'Centro Comercial / Mall', False, [], [], 27),
    ('spa', 'Spa & Bienestar', False, [], [], 28),
    ('store', 'Tienda General', False, [], [], 29),
    ('supermarket', 'Supermercado', False, [], [], 30),
    ('veterinary_care', 'Clínica Veterinaria', False, [], [], 31),
    ('meal_takeout', 'Comida Express / Takeout', True,
     ['Food & Drink quality', 'Service'],
     ['Spend per person'], 32),
    ('general_contractor', 'Constructora / Remodelaciones', False, [], [], 33),
]


RUBROS_MERGED_DEF = [
    # (orden, nombre, tipo, icono, rubro_principal_1, rubro_principal_2, descripcion,
    #  google_category_en (FK), google_categories_ens (M2M list), es_otro)
    (1, 'Cafetería, Brunch y Té', 'LOCAL_FISICO', '☕',
     'SERVICIO', 'PRODUCTO',
     'Cafés, brunch, cafeterías, casas de té, repostería pequeña y coffee shops.',
     'cafe', ['bakery'], False),
    (2, 'Restaurante y Comedor', 'LOCAL_FISICO', '🍽️',
     'SERVICIO', 'PRODUCTO',
     'Restaurantes cocina chilena, internacional, familiar, ejecutiva, cebicherías, sushi.',
     'restaurant', ['meal_delivery', 'meal_takeaway'], False),
    (3, 'Panadería y Pastelería', 'LOCAL_FISICO', '🥐',
     'PRODUCTO', 'SERVICIO',
     'Pan, marraqueta, hallulla, pan amasado, pastelería, panettone, tortas.',
     'bakery', ['cafe'], False),
    (4, 'Bar, Pub y Cervecería', 'LOCAL_FISICO', '🍺',
     'SERVICIO', 'PRODUCTO',
     'Pubs, cervecerías artesanales, tabernas, bares nocturnos, happy hour.',
     'bar', ['restaurant'], False),
    (5, 'Comida Rápida / Fast Food', 'LOCAL_FISICO', '🍔',
     'PRODUCTO', 'SERVICIO',
     'Hamburgueserías, completos, hot-dogs, sándwiches, pollos a las brasas, pizzas.',
     'meal_takeaway', ['meal_delivery', 'restaurant'], False),
    (6, 'Peluquería y Barbería', 'LOCAL_FISICO', '✂️',
     'SERVICIO', None,
     'Peluquerías damas/caballeros, barberías, colorimetría, alisados, extensiones.',
     'hair_care', ['beauty_salon'], False),
    (7, 'Gimnasio y Fitness', 'LOCAL_FISICO', '🏋️',
     'SERVICIO', None,
     'Gimnasios, crossfit, box functional, yoga, pilates, spinning, entrenamiento personal.',
     'gym', [], False),
    (8, 'Spa, Estética y Bienestar', 'LOCAL_FISICO', '💅',
     'SERVICIO', None,
     'Estéticas, spas, uñas, pestañas, depilación, masajes, faciales, wellness.',
     'spa', ['beauty_salon'], False),
    (9, 'Supermercado y Minimarket', 'LOCAL_FISICO', '🛒',
     'PRODUCTO', None,
     'Supermercados, minimarkets, autoservicio, tiendas de abarrotes.',
     'supermarket', ['convenience_store', 'store'], False),
    (10, 'Farmacia y Salud Cotidiana', 'LOCAL_FISICO', '💊',
     'PRODUCTO', 'SERVICIO',
     'Farmacias, sucursales farmacéuticas, perfumerías anexas, salud comunitaria.',
     'pharmacy', ['doctor'], False),
    (11, 'Clínica Médica y Consultorio', 'LOCAL_FISICO', '🏥',
     'SERVICIO', None,
     'Centros médicos, clínicas generales, especialidades, policlínicos, urgencia ambulatoria.',
     'doctor', [], False),
    (12, 'Veterinaria y Clínica Veterinaria', 'LOCAL_FISICO', '🐾',
     'SERVICIO', 'PRODUCTO',
     'Clínicas veterinarias, veterinarias, atención perros/gatos, pet hospital, consultas.',
     'veterinary_care', ['pet_store'], False),
    (13, 'Pet Shop y Tienda Mascotas', 'LOCAL_FISICO', '🐶',
     'PRODUCTO', 'SERVICIO',
     'Tiendas de mascotas, accesorios perros/gatos, alimentos balanceados, zoo tienda, grooming.',
     'pet_store', ['veterinary_care'], False),
    (14, 'Tienda de Ropa y Moda', 'LOCAL_FISICO', '👕',
     'PRODUCTO', 'SERVICIO',
     'Tiendas de ropa dama/varón/niño, jeans, vestuario, moda urbana, outlet.',
     'clothing_store', ['shoe_store'], False),
    (15, 'Zapatería y Calzado', 'LOCAL_FISICO', '👟',
     'PRODUCTO', 'SERVICIO',
     'Zapatillas urbanas/running, zapatería, cinturones, carteras, accesorios vestir.',
     'shoe_store', ['clothing_store'], False),
    (16, 'Ferretería y Construcción', 'LOCAL_FISICO', '🔨',
     'PRODUCTO', 'SERVICIO',
     'Ferreterías, pinturerías, materiales construcción, madereras, herramientas.',
     'hardware_store', ['general_contractor'], False),
    (17, 'Taller Mecánico Automotriz', 'LOCAL_FISICO', '🔧',
     'SERVICIO', None,
     'Talleres mecánicos, eléctricos automotrices, suspensiones, neumáticos, servicio técnico.',
     'car_repair', ['car_wash'], False),
    (18, 'Autolavado y Estética Vehicular', 'LOCAL_FISICO', '🧼',
     'SERVICIO', None,
     'Autolavado, lavado de autos, detailing, estéticas vehiculares, lavado motor.',
     'car_wash', ['car_repair'], False),
    (19, 'Lavandería y Tintorería', 'LOCAL_FISICO', '🧺',
     'SERVICIO', None,
     'Lavandería autoservicio, tintorería, lavado de edredones, planchado, lavandería industrial.',
     'laundry', [], False),
    (20, 'Librería y Papelería', 'LOCAL_FISICO', '📚',
     'PRODUCTO', 'SERVICIO',
     'Librerías, papelerías, útiles escolares, arte, oficina, cuadernos, regalos.',
     'book_store', ['store'], False),
    (21, 'Tienda de Electrónica y Tecnología', 'LOCAL_FISICO', '📱',
     'PRODUCTO', 'SERVICIO',
     'Electrónica de consumo, celulares, computación, electrodomésticos, soporte técnico.',
     'electronics_store', ['store'], False),
    (22, 'Tienda de Muebles y Hogar', 'LOCAL_FISICO', '🛋️',
     'PRODUCTO', 'SERVICIO',
     'Muebles, hogar, decoración, artículos para casa, cocina, dormitorio.',
     'furniture_store', ['home_goods_store'], False),
    (23, 'Floristería y Jardinería', 'LOCAL_FISICO', '💐',
     'PRODUCTO', 'SERVICIO',
     'Floristerías, arreglos florales, rosas, plantas, jardinería, paisajismo, eventos.',
     'florist', [], False),
    (24, 'Joyería y Relojería', 'LOCAL_FISICO', '💎',
     'PRODUCTO', 'SERVICIO',
     'Joyerías, relojerías, anillos, collares, compromiso, oro, plata, relojes.',
     'jewelry_store', [], False),
    (25, 'Centro Comercial y Locales', 'LOCAL_FISICO', '🏬',
     'MIXTO', None,
     'Shopping malls, centros comerciales, strip centers, locales comerciales múltiples rubros.',
     'shopping_mall', ['store'], False),
    (26, 'Licorería y Bebidas', 'LOCAL_FISICO', '🍾',
     'PRODUCTO', None,
     'Licorerías, vinos, cervezas, destilados, whiskys, pisco, bebidas premium.',
     'liquor_store', ['bar'], False),
    (27, 'Hotel, Hostal y Alojamiento', 'LOCAL_FISICO', '🏨',
     'SERVICIO', 'PRODUCTO',
     'Hoteles, apart-hoteles, hostales, bed & breakfast, moteles, cabañas, hospedaje.',
     None, [], False),
    (28, 'Constructora, Inmobiliaria y Servicios Técnicos', 'AMBOS', '🏗️',
     'SERVICIO', None,
     'Constructoras, remodelaciones, inmobiliarias, corredores propiedades, arriendo/venta, ingeniería.',
     'general_contractor', ['hardware_store'], False),
    (29, 'E-Commerce Ropa y Moda', 'RUBRO_ONLINE', '🛍️',
     'PRODUCTO', None,
     'Tiendas online de ropa, moda, calzado, accesorios vestir digitales.',
     'clothing_store', [], False),
    (30, 'E-Commerce Electrónica y Tecnología', 'RUBRO_ONLINE', '💻',
     'PRODUCTO', None,
     'Tiendas online electrónica, celulares, computación, gadgets, tech.',
     'electronics_store', [], False),
    (31, 'E-Commerce Hogar y Decoración', 'RUBRO_ONLINE', '🏠',
     'PRODUCTO', None,
     'Tiendas online hogar, muebles, decoración, cocina, baño.',
     'home_goods_store', [], False),
    (32, 'E-Commerce Deportes y Outdoor', 'RUBRO_ONLINE', '🎽',
     'PRODUCTO', None,
     'Tiendas online deportes, artículos deportivos, camping, bicicletas, outdoor.',
     None, [], False),
    (33, 'E-Commerce Alimentos y Bebidas', 'RUBRO_ONLINE', '🥡',
     'PRODUCTO', None,
     'Tiendas online alimentos, bebidas, gourmet, delivery food, kits cocina.',
     'meal_delivery', ['supermarket'], False),
    (34, 'Servicios Educacionales y Academia', 'AMBOS', '🎓',
     'SERVICIO', None,
     'Cursos, academias idiomas, capacitaciones, formación online, escuelas privadas, coaching.',
     None, [], False),
    (35, 'Servicios Profesionales Legal/Contable', 'AMBOS', '⚖️',
     'SERVICIO', None,
     'Abogados, asesoría legal, notarías, contadores, auditorías, tributario, SII.',
     None, [], False),
    (36, 'Agencia Marketing Digital y Publicidad', 'AMBOS', '📣',
     'SERVICIO', None,
     'Marketing digital, agencias publicidad, community management, diseño gráfico/UX, branding.',
     None, [], False),
    (999, 'Otro (No está en la lista)', 'AMBOS', '➕',
     'MIXTO', None,
     'Usa esta opción si no encuentras tu rubro. El equipo ClientBeat se contactará para agregarlo.',
     None, [], True),
]


DIMENSIONES_TOP_RUBROS = {
    'Cafetería, Brunch y Té': {
        'ATENCION': {
            'nombre': 'Atención al Cliente',
            'descripcion': 'Calidez, amabilidad y eficiencia del personal en barra y mesa.',
            'atributos': [
                ('Amabilidad barista', ['amable', 'simpático', 'atento', 'cordial', 'buena onda', 'trato amable'], 1),
                ('Velocidad servicio', ['rápido', 'lento', 'demoró', 'esperé mucho', 'rápida atención', 'ágil'], 1),
                ('Conocimiento carta', ['sabe recomendar', 'conoce los productos', 'explica bien', 'recomendación'], 1),
                ('Atención personalizada', ['personalizado', 'me recordaron', 'trato único', 'detalles'], 1),
                ('Solución problemas', ['arreglaron', 'solucionaron', 'respondieron', 'queja', 'reclamo', 'disculpa'], 1),
                ('Disponibilidad mesas', ['sin mesa', 'lleno', 'esperar mesa', 'encontramos lugar', 'cupo'], 1),
                ('Orden en pago', ['pagar rápido', 'caja lenta', 'la cuenta', 'demoró la cuenta'], 1),
                ('Idioma y comunicación', ['explicar', 'entendieron', 'escucharon', 'no entienden', 'comunicación'], 1),
            ],
        },
        'PRODUCTO': {
            'nombre': 'Producto (Café + Comida)',
            'descripcion': 'Calidad del café, comida, bebidas y postres ofrecidos.',
            'atributos': [
                ('Calidad del café', ['café rico', 'café malo', 'expreso', 'cortado', 'mocaccino', 'arábica', 'grano'], 1),
                ('Temperatura correcta', ['frío', 'caliente', 'tibio', 'se enfrió', 'temperatura'], 1),
                ('Sabor comida', ['rico', 'sabroso', 'desabrido', 'salado', 'dulce', 'sabor'], 1),
                ('Porción / Cantidad', ['poco', 'mucho', 'porción', 'cantidad', 'pequeño', 'generoso'], 1),
                ('Precio / Valor', ['caro', 'barato', 'precio', 'valor', 'calidad precio', 'cara'], 1),
                ('Frescura / Fresco', ['fresco', 'recalentado', 'recién hecho', 'pasado', 'horneado'], 1),
                ('Variedad de carta', ['variedad', 'menú', 'pocas opciones', 'carta', 'variado'], 1),
                ('Presentación plato', ['bonito', 'presentación', 'visual', 'lindo el plato'], 1),
            ],
        },
        'ESPACIO': {
            'nombre': 'Espacio / Ambiente',
            'descripcion': 'Decoración, iluminación, música y ambientación general del local.',
            'atributos': [
                ('Decoración / Diseño', ['lindo lugar', 'acogedor', 'decoración', 'diseño', 'estilo', 'moderno'], 1),
                ('Iluminación', ['luz', 'iluminación', 'oscuro', 'luminoso', 'luz cálida'], 1),
                ('Música ambiente', ['música', 'ruido', 'alto volumen', 'tranquilo', 'sonido'], 1),
                ('Comodidad asientos', ['cómodo', 'sillas', 'mesa', 'asiento', 'duro', 'espacioso'], 1),
                ('Aire acondicionado / Clima', ['frío local', 'calor', 'aire acondicionado', 'ventilación'], 1),
                ('Conexión Wi-Fi', ['wifi', 'internet', 'señal', 'no entra señal'], 1),
                ('Tomacorrientes / Work-friendly', ['tomacorriente', 'enchufe', 'trabajar', 'notebook', 'laptop'], 1),
                ('Ambiente olfativo', ['olor rico', 'olor a café', 'olor rancio', 'aroma'], 1),
            ],
        },
        'LIMPIEZA': {
            'nombre': 'Limpieza e Higiene',
            'descripcion': 'Limpieza mesas, baños, pisos, utensilios y apariencia general higiénica.',
            'atributos': [
                ('Mesas limpias', ['mesa sucia', 'limpian las mesas', 'platos usados', 'vidrio sucio'], 1),
                ('Baños limpios', ['baño sucio', 'aseo', 'toilet', 'papel', 'jabón', 'sanitario'], 1),
                ('Pisos limpios', ['piso sucio', 'pegajoso', 'mojado', 'resbaloso'], 1),
                ('Vasos y cubiertos', ['vaso sucio', 'mancha', 'servilleta', 'cubiertos'], 1),
                ('Barra ordenada', ['barra desordenada', 'barra sucia', 'cafetera limpia'], 1),
                ('Uniforme personal', ['uniforme limpio', 'personal limpio', 'manchado'], 1),
                ('Zona de colas', ['fila sucia', 'pedidos en el piso', 'orden'], 1),
                ('Reciclaje y basura', ['basurero lleno', 'reciclaje', 'ordenado'], 1),
            ],
        },
    },
    'Restaurante y Comedor': {
        'ATENCION': {
            'nombre': 'Atención al Cliente',
            'descripcion': 'Meseros, recepción, gestión de reserva y servicio a mesa.',
            'atributos': [
                ('Amabilidad mesero', ['mesero amable', 'atento', 'simpático', 'trato mesero'], 1),
                ('Velocidad platos', ['demoró la comida', 'rápido los platos', 'esperé mucho para comer'], 1),
                ('Gestión reserva', ['reserva', 'reservado', 'nos atendieron la reserva', 'perdimos la reserva'], 1),
                ('Recomendaciones platos', ['me recomendó', 'sugerencias', 'sabe la carta', 'recomendación'], 1),
                ('Atención especial / dieta', ['vegetariano', 'celiaco', 'intolerancia', 'alergia', 'especial'], 1),
                ('Servicio en la mesa', ['recoger platos', 'sirvieron agua', 'llenaron el vaso'], 1),
                ('Disculpa ante error', ['se disculpó', 'falló', 'equivocaron de plato', 'error en el pedido'], 1),
                ('Cuenta / Pago', ['la cuenta lenta', 'demoró el pago', 'pagar'], 1),
            ],
        },
        'PRODUCTO': {
            'nombre': 'Comida y Bebidas',
            'descripcion': 'Calidad de platos principales, entradas, postres y copas.',
            'atributos': [
                ('Calidad plato principal', ['rico plato', 'sabroso', 'carné', 'pescado', 'marraqueta'], 1),
                ('Temperatura comida', ['caliente', 'fría la comida', 'tibio', 'recalentado'], 1),
                ('Frescura ingredientes', ['fresco', 'frescura', 'pescado fresco', 'verduras', 'ingrediente'], 1),
                ('Tamaño porción', ['porción grande', 'poca comida', 'tamaño', 'plato lleno'], 1),
                ('Relación calidad-precio', ['caro', 'precio justo', 'calidad precio', 'valor'], 1),
                ('Presentación plato', ['lindo plato', 'presentación', 'bonito', 'plato decorado'], 1),
                ('Bebidas / Bar', ['trago rico', 'bebida', 'vino', 'cerveza fría', 'pisco'], 1),
                ('Postres', ['postre rico', 'postre malo', 'helado', 'pastel', 'postre'], 1),
            ],
        },
        'ESPACIO': {
            'nombre': 'Salón y Ambiente',
            'descripcion': 'Mobiliario, iluminación, música y ambiente general para la experiencia.',
            'atributos': [
                ('Decoración / Estilo', ['acogedor', 'lindo lugar', 'decoración', 'ambiente', 'estilo'], 1),
                ('Espacio entre mesas', ['apretado', 'espacio entre mesas', 'privacidad', 'pegado'], 1),
                ('Iluminación', ['luz', 'oscuro', 'cálida', 'romántico', 'iluminación'], 1),
                ('Música y volumen', ['música', 'ruido', 'volumen', 'música alta', 'conversar'], 1),
                ('Clima / Aire', ['calor', 'frío', 'aire acondicionado', 'ventilación'], 1),
                ('Terraza / Exterior', ['terraza', 'afuera', 'patio', 'exterior'], 1),
                ('Comodidad asiento', ['sillas cómodas', 'mesa', 'duro', 'asiento'], 1),
                ('Olor ambiente', ['olor rico', 'olor a cocina', 'aroma', 'olor rancio'], 1),
            ],
        },
        'LIMPIEZA': {
            'nombre': 'Limpieza e Higiene',
            'descripcion': 'Baño, mesas, cubiertos, manteles y limpieza general del local.',
            'atributos': [
                ('Baños limpios', ['baño sucio', 'aseo', 'inodoro', 'lavatorio', 'jabón'], 1),
                ('Mesas y manteles', ['mesa sucia', 'mantel manchado', 'servilleta'], 1),
                ('Cubiertos y copas', ['vaso sucio', 'cubierto sucio', 'mancha', 'limpio'], 1),
                ('Pisos / Escaleras', ['piso sucio', 'mojado', 'resbaloso', 'escoba'], 1),
                ('Cocina visible', ['cocina abierta', 'cocina limpia', 'cocinero limpio'], 1),
                ('Personal uniforme', ['uniforme limpio', 'personal limpio', 'delantal'], 1),
                ('Zona de espera', ['sala espera sucia', 'ordenado', 'entrada limpia'], 1),
                ('Gestión basuras', ['basurero lleno', 'platos usados', 'orden'], 1),
            ],
        },
    },
    'Panadería y Pastelería': {
        'ATENCION': {
            'nombre': 'Atención en Caja / Mostrador',
            'descripcion': 'Amabilidad y rapidez al atender en mostrador de pan y pastelería.',
            'atributos': [
                ('Amabilidad mostrador', ['amable', 'simpático', 'atento', 'trato', 'cordial'], 1),
                ('Velocidad atención', ['rápido', 'fila larga', 'demoró', 'esperé mucho', 'ágil'], 1),
                ('Conocimiento productos', ['sabe explicar', 'recomienda', 'conoce', 'recomendación'], 1),
                ('Corte / Porcionado', ['cortaron bien', 'porcionar', 'corte delgado', 'corte grueso'], 1),
                ('Empaque correcto', ['bien empaquetado', 'empacaron', 'se desarmó', 'caja rota'], 1),
                ('Precisión pedido', ['equivoqué', 'me dieron otro', 'pedido correcto', 'cambio'], 1),
                ('Atención teléfono / pedido', ['llamar', 'pedido por teléfono', 'no respondieron'], 1),
                ('Formas de pago', ['no acepta tarjeta', 'efectivo', 'transbank', 'mercado pago'], 1),
            ],
        },
        'PRODUCTO': {
            'nombre': 'Pan y Pastelería',
            'descripcion': 'Sabor, frescura, textura y variedad del pan, pastelería y tortas.',
            'atributos': [
                ('Frescura del pan', ['pan fresco', 'pan duro', 'recién salido', 'frescura'], 1),
                ('Sabor del pan', ['marraqueta rica', 'sabor', 'rico', 'desabrido', 'salado'], 1),
                ('Textura / Miga', ['migajón', 'esponjoso', 'crocante', 'miga', 'tostada'], 1),
                ('Calidad pastelería', ['pastel rico', 'torta mala', 'pastelería', 'crema'], 1),
                ('Variedad productos', ['variedad', 'pocas opciones', 'hay de todo', 'gama'], 1),
                ('Relación calidad-precio', ['caro', 'barato', 'precio', 'valor', 'justo'], 1),
                ('Tamaño / Peso', ['pequeño', 'grande', 'pesó', 'tamaño'], 1),
                ('Tortas y productos especiales', ['torta de cumpleaños', 'pedido especial', 'panettone'], 1),
            ],
        },
        'ESPACIO': {
            'nombre': 'Mostrador y Local',
            'descripcion': 'Orden, limpieza visual y orden del mostrador, vitrina y zona de pago.',
            'atributos': [
                ('Vitrina atractiva', ['vitrina linda', 'ordenado el mostrador', 'producto exhibido'], 1),
                ('Orden local', ['desordenado', 'ordenado', 'ordenado local'], 1),
                ('Aroma a pan', ['olor rico', 'olor a pan', 'aroma', 'huele rico'], 1),
                ('Iluminación vitrina', ['iluminación', 'luz', 'luz cálida', 'oscuro'], 1),
                ('Espacio cola', ['fila apretada', 'espacio para fila', 'entrada'], 1),
                ('Zona de consumo / Mesas', ['mesa para comer', 'comer ahí', 'mesitas'], 1),
                ('Estacionamiento cercano', ['estacionar', 'paradero', 'acceso'], 1),
                ('Señaleticia / Precios', ['precio visible', 'etiqueta precio', 'letrero'], 1),
            ],
        },
        'LIMPIEZA': {
            'nombre': 'Limpieza Mostrador y Vitrina',
            'descripcion': 'Limpieza de vitrina, bandejas, pisos y utensilios en contacto con alimento.',
            'atributos': [
                ('Vitrina limpia', ['vitrina sucia', 'vidrio sucio', 'manchas', 'limpia la vitrina'], 1),
                ('Bandejas pan', ['bandeja sucia', 'harina por todas partes', 'ordenado'], 1),
                ('Piso limpio', ['piso con harina', 'piso mojado', 'pegajoso'], 1),
                ('Guantes e higiene personal', ['guantes', 'manos limpias', 'cubrebocas', 'tocó el dinero'], 1),
                ('Utensilios / Pinzas', ['pinza sucia', 'cuchillo limpio'], 1),
                ('Baños (si tienen)', ['baño', 'aseo', 'higiene'], 1),
                ('Empaques limpios', ['bolsa limpia', 'caja limpia', 'papel limpio'], 1),
                ('Zona caja', ['caja limpia', 'mostrador limpio', 'dinero ordenado'], 1),
            ],
        },
    },
    'Bar, Pub y Cervecería': {
        'ATENCION': {
            'nombre': 'Atención Barra y Floor Staff',
            'descripcion': 'Rapidez barman, amabilidad, gestión fila/entrada y atención a la mesa.',
            'atributos': [
                ('Amabilidad barman', ['barman amable', 'bartender', 'simpático', 'atento'], 1),
                ('Velocidad tragos', ['demoró el trago', 'rápido la cerveza', 'esperé mucho en barra'], 1),
                ('Atención mesa', ['mesa atendida', 'mesero', 'pidiendo'], 1),
                ('Gestión fila / Entrada', ['fila larga', 'entré rápido', 'seguridad', 'portero', 'lista'], 1),
                ('Conocimiento de carta tragos', ['recomendó un trago', 'conoce la carta', 'sugiere cerveza'], 1),
                ('Atención en eventos / promociones', ['happy hour', 'promoción', 'descuento', 'evento'], 1),
                ('Seguridad / Ambiente sano', ['seguridad', 'pelea', 'seguro', 'guardia'], 1),
                ('Cuenta / Pago', ['la cuenta', 'carta de cobro', 'pagar', 'propina'], 1),
            ],
        },
        'PRODUCTO': {
            'nombre': 'Bebidas, Tragos y Pinchos',
            'descripcion': 'Calidad y frescura de cerveza, pisco, cócteles y comida bar/pinchos.',
            'atributos': [
                ('Cerveza fría', ['cerveza fría', 'cerveza tibia', 'temperatura', 'helada'], 1),
                ('Trago bien preparado', ['rico trago', 'piscola', 'pisco sour', 'cóctel', 'bien preparado'], 1),
                ('Variedad de carta', ['variedad', 'cerveza artesanal', 'gama', 'carta de tragos'], 1),
                ('Precio bebidas', ['caro', 'precio', 'valor', 'precio alto', 'económico'], 1),
                ('Pinchos / Comida bar', ['papas fritas', 'completo', 'tapa', 'pincho', 'comida bar'], 1),
                ('Dilución / Cantidad alcohol', ['aguado', 'fuerte', 'se pasó de alcohol', 'tibio'], 1),
                ('Vidrio correcto', ['copa adecuada', 'vaso de pinta', 'copa limpia'], 1),
                ('Temperatura ambiente de bebidas', ['frio', 'hielo', 'hielo seco'], 1),
            ],
        },
        'ESPACIO': {
            'nombre': 'Salón, Barra y Ambiente',
            'descripcion': 'Música, luces, tamaño de barra, espacio para bailar/estar de pié.',
            'atributos': [
                ('Música / DJ', ['música buena', 'DJ', 'volumen', 'género musical', 'bailable'], 1),
                ('Iluminación', ['luces', 'iluminación', 'oscuro', 'luces de colores'], 1),
                ('Espacio / Capacidad', ['apretado', 'lugar chico', 'espacioso', 'lugar grande'], 1),
                ('Barra y bancos', ['barra larga', 'bancos', 'lugar en barra'], 1),
                ('Pista de baile', ['pista', 'bailar', 'lugar para bailar'], 1),
                ('Clima / Ventilación', ['calor', 'aire acondicionado', 'huele a humo'], 1),
                ('Terraza / Fuera', ['terraza', 'afuera', 'patio', 'exterior', 'fumar'], 1),
                ('Decoración y estilo', ['lindo lugar', 'acogedor', 'estilo', 'temático'], 1),
            ],
        },
        'LIMPIEZA': {
            'nombre': 'Limpieza Baño y Salón',
            'descripcion': 'Baño, mesas, pisos y limpieza general en horario nocturno.',
            'atributos': [
                ('Baño limpio', ['baño asqueroso', 'aseo baño', 'sin papel', 'jabón'], 1),
                ('Piso limpio / No pegajoso', ['piso pegajoso', 'piso mojado', 'vasos rotos'], 1),
                ('Mesas y vasos', ['mesa llena de vasos', 'vasos vacíos', 'limpiar mesa'], 1),
                ('Vasos / Copas limpias', ['vaso sucio', 'copa con mancha', 'labial'], 1),
                ('Reciclaje y basura', ['basurero lleno', 'botellas', 'latas', 'ordenado'], 1),
                ('Zona fumadores / Terraza', ['cenicero lleno', 'terrible fuera', 'limpio afuera'], 1),
                ('Personal higiene', ['barman limpio', 'uniforme'], 1),
                ('Entrada / Cola', ['entrada limpia', 'ordenado afuera'], 1),
            ],
        },
    },
    'Peluquería y Barbería': {
        'ATENCION': {
            'nombre': 'Atención al Cliente',
            'descripcion': 'Amabilidad, escucha del estilo, recepción y gestión de horas.',
            'atributos': [
                ('Amabilidad peluquero/barbero', ['amable', 'simpático', 'atento', 'buen trato', 'peluquero'], 1),
                ('Escucha / Entiende estilo', ['me entendió', 'escuchó', 'expliqué lo que quería', 'estilo'], 1),
                ('Puntualidad hora', ['demoró', 'esperé mucho', 'puntual', 'a tiempo', 'hora'], 1),
                ('Recepción / Reserva', ['reserva', 'agendar', 'fácil agendar', 'no contestaron'], 1),
                ('Consejo profesional', ['recomendó', 'me aconsejó', 'consejo', 'sugirió'], 1),
                ('Solución problemas / Descontento', ['arreglaron', 'error', 'se disculpó', 'descontento'], 1),
                ('Atención complementaria', ['café', 'agua', 'revista', 'detalle'], 1),
                ('Explicación productos usados', ['producto', 'shampoo', 'tinte', 'explicó'], 1),
            ],
        },
        'PRODUCTO': {
            'nombre': 'Resultado / Técnica',
            'descripcion': 'Corte, color, peinado, barba, calidad del trabajo final y duración.',
            'atributos': [
                ('Corte perfecto / Me gustó', ['me gustó el corte', 'perfecto', 'rico corte', 'corte igual'], 1),
                ('Color / Tinte', ['color bueno', 'tinte mal', 'me quemó', 'color duró'], 1),
                ('Barba y afeitado', ['barba perfecta', 'navaja', 'afeitado', 'barbero'], 1),
                ('Peinado / Lavado', ['peinado rico', 'shampoo', 'masaje cabeza', 'lavado'], 1),
                ('Duración del trabajo', ['duró mucho tiempo', 'muy rápido', 'pausado'], 1),
                ('Precio / Valor', ['caro', 'precio justo', 'valor', 'pagar por servicio'], 1),
                ('Productos usados', ['producto bueno', 'marca', 'shampoo', 'quemó cuero'], 1),
                ('Acabado / Detalles', ['detalles', 'acabado fino', 'terminar de arreglar'], 1),
            ],
        },
        'ESPACIO': {
            'nombre': 'Salón y Sillas',
            'descripcion': 'Comodidad, limpieza visual, música, ambiente del salón/barbería.',
            'atributos': [
                ('Silla cómoda', ['silla', 'cómodo', 'cuero', 'lavacabezas'], 1),
                ('Iluminación y espejos', ['espejo', 'luz', 'iluminación', 'ver bien'], 1),
                ('Música ambiente', ['música', 'volumen', 'música agradable'], 1),
                ('Decoración / Estilo', ['moderno', 'lindo local', 'acogedor', 'estilo barbería'], 1),
                ('Lugar para espera', ['sala espera', 'esperar cómodo', 'esperar de pie'], 1),
                ('Clima y ventilación', ['calor', 'olor a química', 'ventilación', 'tinte olor'], 1),
                ('Privacidad / Ambiente', ['privado', 'todos miran', 'espacio individual'], 1),
                ('Estacionamiento / Acceso', ['paradero', 'accesible', 'entrada fácil'], 1),
            ],
        },
        'LIMPIEZA': {
            'nombre': 'Limpieza e Higiene',
            'descripcion': 'Instrumental, sillas, piso, toallas y limpieza general del salón.',
            'atributos': [
                ('Tijeras / Herramientas limpias', ['tijeras limpias', 'máquina de cortar pelo', 'esterilizado'], 1),
                ('Toallas / Peines', ['toalla limpia', 'peine sucio', 'toalla usada'], 1),
                ('Pelo en el piso', ['pelo por todas partes', 'barrieron', 'pelo en la silla'], 1),
                ('Manteles / Capas', ['capa limpia', 'torta de pelo', 'negro limpio'], 1),
                ('Lavacabezas / Fregadero', ['lavacabezas sucio', 'pelos en lavamanos', 'taponado'], 1),
                ('Baños', ['baño limpio', 'higiene'], 1),
                ('Productos en orden', ['botellas tiradas', 'ordenado', 'estante limpio'], 1),
                ('Uniforme personal', ['uniforme limpio', 'barbero limpio', 'peluquera limpia'], 1),
            ],
        },
    },
    'Gimnasio y Fitness': {
        'ATENCION': {
            'nombre': 'Atención Administración y Profesores',
            'descripcion': 'Recepción, profesor guía, personal trainer y gestión de membresía.',
            'atributos': [
                ('Amabilidad recepción', ['recepcionista amable', 'hola al entrar', 'simpático'], 1),
                ('Profesor / PT competente', ['profesor bueno', 'entrenador', 'sabe enseñar', 'te corrige'], 1),
                ('Planificación / Rutina', ['rutina personalizada', 'me armó un plan', 'no tengo rutina'], 1),
                ('Gestión membresía / Contrato', ['membresía', 'contrato', 'matrícula', 'renovación', 'precio'], 1),
                ('Disponibilidad clases', ['clase de spinning', 'yoga', 'crossfit', 'cupo lleno'], 1),
                ('Asesoría nutricional', ['nutricionista', 'comida', 'dieta', 'asesoría nutricional'], 1),
                ('Solución problemas / Mala experiencia', ['problema', 'reclamo', 'se quejé', 'respuesta'], 1),
                ('Ambiente comunidad / Friendly', ['ambiente sano', 'gente amable', 'clima agradable'], 1),
            ],
        },
        'PRODUCTO': {
            'nombre': 'Equipamiento y Servicios',
            'descripcion': 'Máquinas, pesas, cardio, locker, ducha y servicios de gimnasio.',
            'atributos': [
                ('Máquinas / Equipamiento', ['máquina rota', 'equipamiento bueno', 'cintas', 'mancuernas'], 1),
                ('Cantidad / Variedad', ['pocas máquinas', 'variedad', 'esperar máquina', 'ocupado'], 1),
                ('Locker / Casilleros', ['casillero', 'locker', 'taquilla', 'chapa rota'], 1),
                ('Ducha y Vestuario', ['ducha', 'vestuario', 'baño', 'agua caliente'], 1),
                ('Clases grupales', ['spinning', 'zumba', 'yoga', 'clase rica'], 1),
                ('Piscina / Spa', ['piscina', 'hidromasaje', 'sauna'], 1),
                ('Relación calidad precio', ['precio', 'caro', 'valor', 'membresía cara'], 1),
                ('Horario y disponibilidad', ['horario 24/7', 'abre temprano', 'cierra tarde'], 1),
            ],
        },
        'ESPACIO': {
            'nombre': 'Espacio, Aforo y Ambiente',
            'descripcion': 'Tamaño, distribución, ventilación, música y limpieza general del gim.',
            'atributos': [
                ('Espacio amplio / Lugar', ['apretado', 'espacio', 'chico', 'grande', 'abundante'], 1),
                ('Música ambiente', ['música', 'volumen alto', 'motivador', 'gimnasio música'], 1),
                ('Aire acondicionado / Ventilación', ['olor a sudor', 'calor', 'aire acondicionado', 'ventilación'], 1),
                ('Iluminación', ['luz', 'oscuro', 'luminoso', 'ver bien'], 1),
                ('Zonas diferenciadas', ['zona cardio', 'zona peso', 'zona funcional', 'estiramiento'], 1),
                ('Espejos', ['espejo', 'ver técnica', 'pared de espejos'], 1),
                ('Aforo / Gente en hora punta', ['lleno', 'hora punta', 'poca gente', 'aforado'], 1),
                ('Estacionamiento / Acceso', ['paradero', 'estacionar', 'ubicación'], 1),
            ],
        },
        'LIMPIEZA': {
            'nombre': 'Limpieza e Higiene del Gimnasio',
            'descripcion': 'Máquinas, duchas, piso, toallas y limpieza general del gimnasio.',
            'atributos': [
                ('Máquinas / Equipo limpio', ['máquina con sudor', 'paño para limpiar', 'desinfectante'], 1),
                ('Duchas / Vestuarios', ['ducha sucia', 'hongo', 'mojado', 'limpio vestuario'], 1),
                ('Piso limpio', ['piso con polvo', 'churros de polvo', 'barrido', 'suelo'], 1),
                ('Baños / Inodoros', ['baño asqueroso', 'papel', 'jabón', 'inodoro'], 1),
                ('Toallas dispensadores', ['toalla', 'sin toallas', 'toalla limpia'], 1),
                ('Colchonetas / Tapetes', ['colchoneta sucia', 'tapete', 'yoga mat'], 1),
                ('Olores / Ambiente', ['olor a sudor', 'olor feo', 'desinfectante', 'aroma'], 1),
                ('Basuras ordenadas', ['basurero lleno', 'botellas plásticas', 'ordenado'], 1),
            ],
        },
    },
}


class Command(BaseCommand):
    help = (
        'Carga / actualiza: (1) 33 Google Categories (Google Places API, 33 principales con subratings), '
        '(2) 36 Rubros merged (26 CSV + 28 Metodología + extras chilenos), '
        '(3) 4 Dimensiones × 6 Rubros TOP = 24 dimensiones, '
        '(4) 8 Atributos c/u × 24 dimensiones = ~192 atributos con keywords sinónimos para matcher de reseñas. '
        'Usa --reset para limpiar y recargar todo.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra GoogleCategory / RubroDimension / RubroDimensionAtributo / Rubro y vuelve a insertar.',
        )

    def handle(self, *args, **options):
        reset = options.get('reset')

        if reset:
            self.stdout.write('[INFO] Reset solicitado: borrando Rubros / Dimensions / Atributos / GoogleCategory...')
            RubroDimensionAtributo.objects.all().delete()
            RubroDimension.objects.all().delete()
            Rubro.objects.all().delete()
            GoogleCategory.objects.all().delete()

        # ================================================
        # PASO 1: GoogleCategory
        # ================================================
        self.stdout.write('[1/4] Cargando GoogleCategory (33 principales)...')
        gc_creados = gc_actualizados = 0
        google_en_to_obj = {}
        for google_en, google_es, has_sub, sub_ex, add_fields, orden in GOOGLE_CATEGORIES_DEF:
            obj, created = GoogleCategory.objects.get_or_create(
                google_en=google_en,
                defaults={
                    'google_es': google_es,
                    'has_visible_subratings': has_sub,
                    'subratings_examples': sub_ex,
                    'additional_fields': add_fields,
                    'orden': orden,
                    'activo': True,
                }
            )
            google_en_to_obj[google_en] = obj
            if created:
                gc_creados += 1
                continue
            changed = False
            for attr, val in [
                ('google_es', google_es),
                ('has_visible_subratings', has_sub),
                ('subratings_examples', sub_ex),
                ('additional_fields', add_fields),
                ('orden', orden),
                ('activo', True),
            ]:
                if getattr(obj, attr) != val:
                    setattr(obj, attr, val)
                    changed = True
            if changed:
                obj.save()
                gc_actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'   → GoogleCategory: {gc_creados} creados, {gc_actualizados} actualizados, total {GoogleCategory.objects.count()}'
        ))

        # ================================================
        # PASO 2: Rubros merged
        # ================================================
        self.stdout.write('[2/4] Cargando Rubros merged (36 = 26 CSV + 28 Metodología + extras)...')
        rubros_creados = rubros_actualizados = 0
        rubro_nombre_to_obj = {}
        for (
            orden, nombre, tipo, icono, rp1, rp2, descripcion,
            gcat_en_fk, gcat_ens_m2m, es_otro,
        ) in RUBROS_MERGED_DEF:
            slug = slugify(nombre)
            defaults = {
                'slug': slug,
                'tipo': tipo,
                'icono': icono,
                'rubro_principal_1': rp1,
                'rubro_principal_2': rp2,
                'descripcion': descripcion,
                'activo': True,
                'es_otro': es_otro,
                'orden': orden,
            }
            if gcat_en_fk and gcat_en_fk in google_en_to_obj:
                defaults['google_category'] = google_en_to_obj[gcat_en_fk]
            rubro, created = Rubro.objects.get_or_create(nombre=nombre, defaults=defaults)
            rubro_nombre_to_obj[nombre] = rubro
            if created:
                rubros_creados += 1
                self._update_rubro_m2m(rubro, gcat_ens_m2m, google_en_to_obj)
                continue
            changed = False
            for attr, val in defaults.items():
                if attr == 'google_category' and val is None:
                    continue
                if getattr(rubro, attr) != val:
                    setattr(rubro, attr, val)
                    changed = True
            if changed:
                rubro.save()
                rubros_actualizados += 1
            self._update_rubro_m2m(rubro, gcat_ens_m2m, google_en_to_obj)

        self.stdout.write(self.style.SUCCESS(
            f'   → Rubros: {rubros_creados} creados, {rubros_actualizados} actualizados, total {Rubro.objects.count()}'
        ))

        # ================================================
        # PASO 3: RubroDimension por rubros TOP
        # ================================================
        self.stdout.write('[3/4] Cargando RubroDimension para 6 rubros TOP (Cafetería, Restaurante, Panadería, Bar, Peluquería, Gimnasio)...')
        dim_creados = dim_actualizados = 0
        rubro_dim_to_obj = {}
        for rubro_nombre, dims_map in DIMENSIONES_TOP_RUBROS.items():
            if rubro_nombre not in rubro_nombre_to_obj:
                self.stdout.write(self.style.WARNING(f'   → Omite dimensiones de {rubro_nombre}, rubro no existe en merged list'))
                continue
            rubro = rubro_nombre_to_obj[rubro_nombre]
            for idx, (tipo_key, dim_def) in enumerate(dims_map.items(), start=1):
                tipo_valor = tipo_key
                nombre_dim = dim_def['nombre']
                desc_dim = dim_def['descripcion']
                dkey = (rubro_nombre, nombre_dim)
                dim, created = RubroDimension.objects.get_or_create(
                    rubro=rubro,
                    nombre=nombre_dim,
                    defaults={
                        'tipo': tipo_valor,
                        'descripcion': desc_dim,
                        'orden': idx,
                    }
                )
                rubro_dim_to_obj[dkey] = dim
                if created:
                    dim_creados += 1
                    continue
                changed = False
                for attr, val in [('tipo', tipo_valor), ('descripcion', desc_dim), ('orden', idx)]:
                    if getattr(dim, attr) != val:
                        setattr(dim, attr, val)
                        changed = True
                if changed:
                    dim.save()
                    dim_actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'   → Dimensiones: {dim_creados} creadas, {dim_actualizados} actualizadas, total {RubroDimension.objects.count()}'
        ))

        # ================================================
        # PASO 4: RubroDimensionAtributo por dimensión
        # ================================================
        self.stdout.write('[4/4] Cargando RubroDimensionAtributo (8 atributos x dimensión x 6 rubros TOP)...')
        attr_creados = attr_actualizados = 0
        for rubro_nombre, dims_map in DIMENSIONES_TOP_RUBROS.items():
            for tipo_key, dim_def in dims_map.items():
                dkey = (rubro_nombre, dim_def['nombre'])
                if dkey not in rubro_dim_to_obj:
                    continue
                dim_obj = rubro_dim_to_obj[dkey]
                for idx_a, (nombre_attr, sinonimos, pond) in enumerate(dim_def['atributos'], start=1):
                    attr, created = RubroDimensionAtributo.objects.get_or_create(
                        dimension=dim_obj,
                        nombre=nombre_attr,
                        defaults={
                            'sinonimos': sinonimos,
                            'ponderacion': pond,
                            'orden': idx_a,
                        }
                    )
                    if created:
                        attr_creados += 1
                        continue
                    changed = False
                    for a, v in [('sinonimos', sinonimos), ('ponderacion', pond), ('orden', idx_a)]:
                        if getattr(attr, a) != v:
                            setattr(attr, a, v)
                            changed = True
                    if changed:
                        attr.save()
                        attr_actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'   → Atributos: {attr_creados} creados, {attr_actualizados} actualizados, total {RubroDimensionAtributo.objects.count()}'
        ))

        # ================================================
        # RESUMEN FINAL
        # ================================================
        total_rubros_activo = Rubro.objects.filter(activo=True).count()
        total_top_rubro_dim = RubroDimension.objects.filter(
            rubro__nombre__in=list(DIMENSIONES_TOP_RUBROS.keys())
        ).count()
        total_es_otro = Rubro.objects.filter(es_otro=True).count()
        total_google_subratings = GoogleCategory.objects.filter(has_visible_subratings=True).count()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 72))
        self.stdout.write(self.style.SUCCESS('  RESULTADO FINAL SEED RUBROS + GOOGLE CAT + DIMENSIONES + ATRIBUTOS'))
        self.stdout.write(self.style.SUCCESS('=' * 72))
        self.stdout.write(f'   GoogleCategory total:              {GoogleCategory.objects.count()}')
        self.stdout.write(f'   GoogleCategory c/ subratings:      {total_google_subratings}')
        self.stdout.write(f'   Rubros merged total:               {Rubro.objects.count()}')
        self.stdout.write(f'   Rubros activos onboarding:         {total_rubros_activo}')
        self.stdout.write(f'   Rubros opción "Otro":              {total_es_otro}')
        self.stdout.write(f'   RubroDimension (6 TOP × 4D):       {RubroDimension.objects.count()} (top6 tiene {total_top_rubro_dim})')
        self.stdout.write(f'   RubroDimensionAtributo (8 x dim):  {RubroDimensionAtributo.objects.count()}')
        self.stdout.write(self.style.SUCCESS('=' * 72))

    def _update_rubro_m2m(self, rubro, gcat_ens_list, google_en_to_obj):
        if not gcat_ens_list:
            return
        objs = []
        for en in gcat_ens_list:
            if en in google_en_to_obj:
                objs.append(google_en_to_obj[en])
        if objs:
            rubro.google_categories.set(objs)
