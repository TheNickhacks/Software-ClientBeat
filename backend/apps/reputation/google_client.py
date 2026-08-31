import logging
import time
import random
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('clientbeat')


@dataclass
class GooglePlaceReview:
    google_review_id: str
    autor_nombre: str
    autor_foto_url: Optional[str]
    calificacion: int
    comentario: Optional[str]
    fecha_google: datetime
    autor_url: Optional[str] = None

    @staticmethod
    def _hash_id(parts: list) -> str:
        h = hashlib.sha1('|'.join(str(p) for p in parts).encode('utf-8')).hexdigest()
        return f'GR-{h}'


@dataclass
class GooglePlace:
    place_id: str
    nombre: str
    direccion: Optional[str]
    rating: Optional[Decimal]
    numero_opiniones: Optional[int]
    latitud: Optional[Decimal]
    longitud: Optional[Decimal]
    rubro_google: Optional[str]
    comuna: Optional[str]
    opiniones: List[GooglePlaceReview] = field(default_factory=list)


class GooglePlacesClientError(Exception):
    pass


class GooglePlacesClient:
    BASE_NEW = 'https://places.googleapis.com/v1'
    BASE_LEGACY = 'https://maps.googleapis.com/maps/api/place'

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_new_api: Optional[bool] = None,
        rate_limit_per_second: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GOOGLE_PLACES_API_KEY
        self.use_new_api = use_new_api if use_new_api is not None else settings.GOOGLE_PLACES_USE_NEW_API
        self.rate_limit_per_second = rate_limit_per_second or settings.GOOGLE_PLACES_RATE_LIMIT_PER_SECOND
        self.max_retries = max_retries or settings.GOOGLE_PLACES_MAX_RETRIES
        self._last_request_at = 0.0

    # --------- internals ---------
    def _throttle(self):
        if self.rate_limit_per_second <= 0:
            return
        min_interval = 1.0 / self.rate_limit_per_second
        now = time.time()
        wait = min_interval - (now - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.time()

    def _request(self, method: str, url: str, *, params: Optional[dict] = None, json_body: Optional[dict] = None) -> dict:
        try:
            import requests  # type: ignore
        except ImportError:  # pragma: no cover
            raise GooglePlacesClientError(
                'La librería `requests` no está instalada. Instálala con `pip install requests` para modo Live.'
            )
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                if method.upper() == 'GET':
                    resp = requests.get(url, params=params, timeout=30)
                elif method.upper() == 'POST':
                    headers = {
                        'Content-Type': 'application/json',
                        'X-Goog-Api-Key': self.api_key,
                    }
                    if self.use_new_api and 'places.googleapis.com' in url:
                        headers.setdefault('X-Goog-FieldMask', '*')
                    resp = requests.post(url, params=params, json=json_body, headers=headers, timeout=30)
                else:  # pragma: no cover
                    raise ValueError(f'Método HTTP no soportado: {method}')

                if resp.status_code == 429:
                    wait_s = min(2 ** attempt, 15)
                    logger.warning('Google Places rate limit 429. Reintento %s/%s en %ss', attempt, self.max_retries, wait_s)
                    time.sleep(wait_s)
                    continue
                if resp.status_code >= 500:
                    wait_s = min(2 ** attempt, 10)
                    logger.warning('Google Places server error %s. Reintento %s/%s en %ss', resp.status_code, attempt, self.max_retries, wait_s)
                    time.sleep(wait_s)
                    continue

                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_exc = e
                wait_s = min(2 ** attempt, 10)
                logger.warning('Google Places error intento %s/%s: %s. Espera %ss', attempt, self.max_retries, e, wait_s)
                time.sleep(wait_s)
        raise GooglePlacesClientError(f'Google Places falló después de {self.max_retries} intentos: {last_exc}')

    # --------- high level public ---------
    def search_places_text(self, query: str, language: str = 'es-CL', region_code: str = 'CL', max_results: int = 10) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise GooglePlacesClientError('GOOGLE_PLACES_API_KEY no está configurada.')
        if self.use_new_api:
            url = f'{self.BASE_NEW}/places:searchText'
            body = {
                'textQuery': query,
                'languageCode': language,
                'regionCode': region_code,
                'pageSize': max_results,
            }
            data = self._request('POST', url, json_body=body)
            return list(data.get('places', []) or [])
        else:  # legacy
            url = f'{self.BASE_LEGACY}/textsearch/json'
            params = {
                'query': query,
                'language': language,
                'region': region_code,
                'key': self.api_key,
            }
            data = self._request('GET', url, params=params)
            return list(data.get('results', []) or [])

    def get_place_details(self, place_id: str, language: str = 'es-CL') -> Optional[Dict[str, Any]]:
        if not self.api_key:
            raise GooglePlacesClientError('GOOGLE_PLACES_API_KEY no está configurada.')
        if self.use_new_api:
            url = f'{self.BASE_NEW}/places/{place_id}'
            params = {'languageCode': language}
            return self._request('GET', url, params=params)
        else:
            url = f'{self.BASE_LEGACY}/details/json'
            params = {
                'place_id': place_id,
                'language': language,
                'fields': 'place_id,name,formatted_address,geometry,rating,user_ratings_total,reviews,types',
                'key': self.api_key,
            }
            data = self._request('GET', url, params=params)
            return data.get('result')

    def _reviews_from_place_dict(self, place: dict, place_id: str) -> List[GooglePlaceReview]:
        reviews_raw = place.get('reviews') or []
        out: List[GooglePlaceReview] = []
        for r in reviews_raw:
            author = r.get('author_name') or 'Usuario Google'
            rating = int(r.get('rating') or 0)
            text = r.get('text') or ''
            time_seconds = r.get('time')
            if time_seconds:
                from datetime import timezone as dt_timezone
                fecha = datetime.fromtimestamp(int(time_seconds), tz=dt_timezone.utc)
            else:
                fecha = timezone.now() - timedelta(days=random.randint(1, 180))
            rid = GooglePlaceReview._hash_id([
                place_id, author, rating, text, int(fecha.timestamp())
            ])
            out.append(GooglePlaceReview(
                google_review_id=rid,
                autor_nombre=author,
                autor_foto_url=r.get('profile_photo_url') or None,
                calificacion=rating,
                comentario=text or None,
                fecha_google=fecha,
                autor_url=r.get('author_url') or None,
            ))
        return out

    def get_place(self, place_id: str) -> Optional[GooglePlace]:
        details = self.get_place_details(place_id)
        if not details:
            return None
        reviews = self._reviews_from_place_dict(details, place_id)
        rating = details.get('rating')
        rating_d = Decimal(str(rating)) if rating is not None else None
        lat = lon = None
        if self.use_new_api:
            loc = (details.get('location') or {}).get('latLng') or {}
            if 'latitude' in loc:
                lat = Decimal(str(loc['latitude']))
            if 'longitude' in loc:
                lon = Decimal(str(loc['longitude']))
            address = details.get('formattedAddress')
            types = details.get('types') or []
            rubro = types[0] if types else None
            comuna = None
            for comp in details.get('addressComponents') or []:
                types_comp = comp.get('types') or []
                if 'locality' in types_comp:
                    comuna = (comp.get('shortText') or comp.get('text') or None)
                    break
        else:
            geo = (details.get('geometry') or {}).get('location') or {}
            if 'lat' in geo:
                lat = Decimal(str(geo['lat']))
            if 'lng' in geo:
                lon = Decimal(str(geo['lng']))
            address = details.get('formatted_address')
            types = details.get('types') or []
            rubro = types[0] if types else None
            comuna = None
        total = details.get('user_ratings_total')
        return GooglePlace(
            place_id=place_id,
            nombre=details.get('name') or '',
            direccion=address,
            rating=rating_d,
            numero_opiniones=int(total) if total is not None else None,
            latitud=lat,
            longitud=lon,
            rubro_google=rubro,
            comuna=comuna,
            opiniones=reviews,
        )


class MockGooglePlacesClient(GooglePlacesClient):
    COMUNAS_COMPETENCIA = [
        'Providencia', 'Las Condes', 'Santiago', 'Ñuñoa', 'La Florida',
        'Viña del Mar', 'Valparaíso', 'Rancagua',
    ]

    NOMBRES_AUTORES = [
        'María González', 'Juan Pérez', 'Camila Rojas', 'Sebastián Muñoz',
        'Francisca Soto', 'Matías López', 'Valentina Fernández', 'Andrés Díaz',
        'Consuelo Martínez', 'Felipe Araya', 'Antonia Paredes', 'Diego Cordero',
    ]

    COMENTARIOS_POOL = {
        5: [
            'Excelente atención y muy buena comida. Volveré sin dudar.',
            'Todo espectacular, desde la atención hasta el café. 100% recomendable.',
            'Mi lugar favorito. El personal siempre amable y los productos son de primera.',
            'Muy buena experiencia. Limpio, ordenado y rápido. 10/10.',
        ],
        4: [
            'Muy buena opción. Precios justos y atención amable. Un par de detalles pero en general bien.',
            'Buen servicio y calidad. A veces hay que esperar un poco pero vale la pena.',
            'Agradable sorpresa. Recomendado para pasar el rato.',
        ],
        3: [
            'Normal. Ni bueno ni malo. Puede mejorar en algunos detalles.',
            'Regular. El precio está bien pero la atención fue mixta.',
            'Estuvo bien, esperaba un poco más por lo que cobran.',
        ],
        2: [
            'No cumplió mis expectativas. Demoró mucho y el pedido llegó incompleto.',
            'Mala atención. La comida era justita. No creo volver.',
            'Falta de limpieza y personal poco amable.',
        ],
        1: [
            'Pésima experiencia. Tuve que reclamar por todo. No lo recomiendo.',
            'Terrible. Pedí algo y me trajeron otra cosa. La atención fue pésima.',
            'No volvería jamás. El producto fue malo y sin solución.',
        ],
    }

    NOMBRES_LOCALES_SUFIJOS = [
        'Express', 'Premium', 'Del Valle', 'Plaza', 'Central', 'Avenida',
        'El Parque', 'Vitacura', 'Providencia', 'Centro', 'Sur', 'Norte',
    ]

    @property
    def MOCK_BASE_DATETIME(self):
        from datetime import timezone as dt_timezone
        return datetime(2026, 8, 30, 12, 0, 0, tzinfo=dt_timezone.utc)

    def __init__(self, *args, **kwargs):
        super().__init__(api_key='MOCK-KEY', *args, **kwargs)
        self._rng = random.Random(20260830)
        logger.info('[MOCK Google Places] iniciado. Respuestas fake determinísticas. Seed=20260830')

    # --------- override public methods ---------
    def search_places_text(self, query: str, language: str = 'es-CL', region_code: str = 'CL', max_results: int = 10) -> List[Dict[str, Any]]:
        time.sleep(0.08)
        base = [w.capitalize() for w in (query or '').split()[:3]] or ['Local', 'Demo']
        rubro_part = ' '.join(base)
        self._rng.seed(int(hashlib.sha1(query.encode('utf-8')).hexdigest()[:8], 16) % (2**32), version=2)
        results = []
        n = min(max_results, 8)
        for i in range(n):
            sufijo = self.NOMBRES_LOCALES_SUFIJOS[i % len(self.NOMBRES_LOCALES_SUFIJOS)]
            comuna = self.COMUNAS_COMPETENCIA[i % len(self.COMUNAS_COMPETENCIA)]
            place_id = f'CH-{hashlib.sha1(f"{rubro_part}{sufijo}{i}".encode()).hexdigest()[:18].upper()}'
            rating = round(self._rng.uniform(3.1, 4.9), 1)
            reviews_count = self._rng.randint(8, 520)
            results.append({
                'name': f'{rubro_part} {sufijo}',
                'id': place_id,
                'place_id': place_id,
                'formattedAddress': f'{self._rng.randint(10, 9999)} Av. Principal, {comuna}, Chile',
                'rating': rating,
                'user_ratings_total': reviews_count,
                'types': [rubro_part.lower().split()[0] if rubro_part else 'restaurant', 'establishment'],
            })
        return results

    def get_place_details(self, place_id: str, language: str = 'es-CL') -> Optional[Dict[str, Any]]:
        time.sleep(0.05)
        self._rng.seed(int(hashlib.sha1(place_id.encode()).hexdigest()[:8], 16) % (2**32))
        nombre = self._generate_name_from_place(place_id)
        comuna = self._rng.choice(self.COMUNAS_COMPETENCIA)
        rating = round(self._rng.uniform(3.0, 4.9), 1)
        reviews_count = self._rng.randint(10, 600)
        lat = Decimal('-33.') + Decimal(self._rng.randint(40000, 46000)) / Decimal('100000')
        lon = Decimal('-70.') + Decimal(self._rng.randint(50000, 70000)) / Decimal('100000')
        reviews = self._generate_mock_reviews(place_id, reviews_count)
        return {
            'name': nombre,
            'place_id': place_id,
            'id': place_id,
            'formattedAddress': f'{self._rng.randint(50, 9999)} Calle Demo, {comuna}, Chile',
            'rating': rating,
            'user_ratings_total': reviews_count,
            'types': ['restaurant', 'food', 'point_of_interest', 'establishment'],
            'reviews': reviews,
            'geometry': {
                'location': {'lat': float(lat), 'lng': float(lon)},
            },
            'location': {'latLng': {'latitude': float(lat), 'longitude': float(lon)}},
            'addressComponents': [
                {'types': ['locality'], 'shortText': comuna, 'text': comuna},
                {'types': ['country'], 'shortText': 'CL', 'text': 'Chile'},
            ],
        }

    def _generate_name_from_place(self, place_id: str) -> str:
        options = ['Café', 'Restaurant', 'Bistrô', 'Pastelería', 'Deli', 'Pub', 'Food & Co', 'La Casona']
        idx = int(hashlib.sha1(place_id.encode()).hexdigest()[:6], 16) % len(options)
        suf = self.NOMBRES_LOCALES_SUFIJOS[(idx + 1) % len(self.NOMBRES_LOCALES_SUFIJOS)]
        return f'{options[idx]} {suf}'

    def _generate_mock_reviews(self, place_id: str, total_google_reviews: int) -> List[Dict[str, Any]]:
        self._rng.seed(int(hashlib.sha1(('r-' + place_id).encode('utf-8')).hexdigest()[:8], 16) % (2**32))
        num_reviews = min(max(5, min(int(total_google_reviews * 0.08) + self._rng.randint(2, 5), 20)), 20)
        dist = [5] * 60 + [4] * 25 + [3] * 8 + [2] * 5 + [1] * 2
        reviews = []
        for i in range(num_reviews):
            author = self._rng.choice(self.NOMBRES_AUTORES)
            rating = self._rng.choice(dist)
            text_pool = self.COMENTARIOS_POOL.get(rating, [])
            text = self._rng.choice(text_pool) if text_pool else ''
            dias = self._rng.randint(0, 210)
            fecha = self.MOCK_BASE_DATETIME - timedelta(days=dias, hours=self._rng.randint(0, 23), minutes=self._rng.randint(0, 59))
            author_photo_hash = hashlib.sha1(author.encode()).hexdigest()[:8]
            reviews.append({
                'author_name': author,
                'author_url': f'https://maps.google.com/maps/contrib/{self._rng.randint(10**15, 10**17 - 1)}',
                'profile_photo_url': f'https://i.pravatar.cc/120?img={(i % 70) + 1}&u={author_photo_hash}',
                'language': 'es',
                'original_language': 'es',
                'rating': rating,
                'relative_time_description': f'hace {dias} días',
                'text': text,
                'time': int(fecha.timestamp()),
                'translated': False,
            })
        reviews.sort(key=lambda r: r['time'], reverse=True)
        return reviews


def get_google_places_client() -> GooglePlacesClient:
    if settings.USE_MOCK_GOOGLE_PLACES:
        return MockGooglePlacesClient()
    return GooglePlacesClient()
