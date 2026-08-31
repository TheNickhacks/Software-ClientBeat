import logging
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
from django.db import transaction

from apps.businesses.models import Local, Negocio
from apps.geo.models import Rubro, Comuna
from apps.reputation.models import ResenaGoogle, Benchmark, SentimientoChoices
from apps.reputation.google_client import (
    get_google_places_client,
    GooglePlacesClient,
    GooglePlace,
    GooglePlaceReview,
)
from apps.sentiment.models import DiccionarioSentimiento, PolaridadChoices

logger = logging.getLogger('clientbeat')


@dataclass
class SyncLocalResult:
    local_id: str
    nombre: str
    place_id_usado: Optional[str]
    nuevas_resenas: int
    actualizadas_resenas: int
    skip_duplicadas: int
    rating_sync_ok: bool
    error: Optional[str] = None


@dataclass
class CompetidorPlace:
    nombre: str
    place_id: str
    rating: Optional[Decimal]
    numero_opiniones: Optional[int]
    direccion: Optional[str]
    puntuacion_orden: Tuple[float, float, float]


PATRON_TOKEN = re.compile(r"[A-Za-z0-9_ÁÉÍÓÚáéíóúñÑüÜ]+", re.UNICODE)


class AnalizadorSentimientoSimple:
    _cache: Optional[Dict[str, Tuple[str, Decimal]]] = None

    @classmethod
    def _cargar(cls) -> Dict[str, Tuple[str, Decimal]]:
        if cls._cache is not None:
            return cls._cache
        mapa: Dict[str, Tuple[str, Decimal]] = {}
        for e in DiccionarioSentimiento.objects.all().only('palabra', 'polaridad', 'peso'):
            try:
                mapa[str(e.palabra).strip().lower()] = (e.polaridad, Decimal(e.peso or 1))
            except Exception:
                continue
        cls._cache = mapa
        return mapa

    @classmethod
    def analizar(cls, texto: Optional[str]) -> Tuple[Optional[str], Optional[Decimal]]:
        if not texto:
            return None, None
        dicc = cls._cargar()
        if not dicc:
            return None, None
        tokens = [m.group(0).lower() for m in PATRON_TOKEN.finditer(texto)]
        score = Decimal('0')
        peso_acum = Decimal('0')
        for token in tokens:
            if token in dicc:
                pol, peso = dicc[token]
                if pol == PolaridadChoices.POSITIVO:
                    val = Decimal('1')
                elif pol == PolaridadChoices.NEGATIVO:
                    val = Decimal('-1')
                else:
                    val = Decimal('0')
                score += val * (peso or Decimal('1'))
                peso_acum += Decimal('1') * (peso or Decimal('1'))
        if peso_acum == 0:
            return None, None
        final = (score / peso_acum).quantize(Decimal('0.01'))
        if final > Decimal('0.15'):
            return SentimientoChoices.POSITIVO, final
        if final < Decimal('-0.15'):
            return SentimientoChoices.NEGATIVO, final
        return SentimientoChoices.NEUTRO, final


class GooglePlacesSyncService:
    def __init__(self, client: Optional[GooglePlacesClient] = None):
        self.client = client or get_google_places_client()

    # --------- helpers place_id ---------
    def _resolver_place_id(self, local: Local) -> Optional[str]:
        if local.google_place_id:
            return local.google_place_id
        # construir query con texto
        partes = [local.nombre]
        if local.comuna:
            partes.append(str(local.comuna))
        elif local.ciudad:
            partes.append(local.ciudad)
        query = ', '.join(p for p in partes if p)
        try:
            resultados = self.client.search_places_text(query, max_results=3)
        except Exception as e:
            logger.warning('No se pudo resolver place_id por texto para Local %s: %s', local.id, e)
            return None
        if not resultados:
            return None
        top = resultados[0]
        pid = top.get('place_id') or top.get('id')
        if pid:
            try:
                local.google_place_id = pid
                local.save(update_fields=['google_place_id'])
            except Exception:
                pass
        return pid

    # --------- upsert reseñas ---------
    @transaction.atomic
    def _upsert_resenas(self, local: Local, opiniones: List[GooglePlaceReview]) -> Tuple[int, int, int]:
        nuevas = 0
        actualizadas = 0
        skip = 0
        for rev in opiniones:
            qs = ResenaGoogle.objects.filter(
                local=local,
                google_review_id=rev.google_review_id,
            )
            existente = qs.first()
            sent, score = AnalizadorSentimientoSimple.analizar(rev.comentario)
            data = dict(
                autor_nombre=rev.autor_nombre,
                autor_foto_url=rev.autor_foto_url,
                calificacion=rev.calificacion,
                comentario=rev.comentario,
                fecha_google=rev.fecha_google,
            )
            if sent is not None:
                data['sentimiento'] = sent
            if score is not None:
                data['score_sentimiento'] = score
            if existente is None:
                ResenaGoogle.objects.create(
                    local=local,
                    google_review_id=rev.google_review_id,
                    **data,
                )
                nuevas += 1
            else:
                cambiado = False
                for k, v in data.items():
                    if getattr(existente, k, None) != v:
                        setattr(existente, k, v)
                        cambiado = True
                if cambiado:
                    existente.save(update_fields=list(data.keys()))
                    actualizadas += 1
                else:
                    skip += 1
        return nuevas, actualizadas, skip

    # --------- benchmark competencia ---------
    def buscar_competencia(self, local: Local, max_resultados: int = 10) -> List[CompetidorPlace]:
        rubro_txt = ''
        comuna_txt = ''
        negocio: Optional[Negocio] = getattr(local, 'negocio', None)
        if negocio:
            rubro = getattr(negocio, 'rubro', None)
            if rubro:
                rubro_txt = str(rubro.nombre) if getattr(rubro, 'nombre', None) else str(rubro)
        if not rubro_txt and negocio and getattr(negocio, 'rubro_google', None):
            rubro_txt = str(negocio.rubro_google)
        if local.comuna:
            comuna_txt = str(local.comuna.nombre) if hasattr(local.comuna, 'nombre') else str(local.comuna)
        elif local.ciudad:
            comuna_txt = local.ciudad
        if not rubro_txt:
            rubro_txt = 'local'
        query = f'{rubro_txt} {comuna_txt} Chile'.strip()
        try:
            resultados = self.client.search_places_text(query, max_results=max_resultados + 2)
        except Exception as e:
            logger.warning('Error buscando competencia Local %s: %s', local.id, e)
            return []
        salida: List[CompetidorPlace] = []
        for r in resultados:
            pid = r.get('place_id') or r.get('id')
            if not pid:
                continue
            if pid == local.google_place_id:
                continue
            rating_raw = r.get('rating')
            rating = Decimal(str(rating_raw)) if rating_raw is not None else None
            opiniones = r.get('user_ratings_total')
            try:
                opiniones_int = int(opiniones) if opiniones is not None else None
            except Exception:
                opiniones_int = None
            direccion = r.get('formattedAddress') or r.get('formatted_address')
            rating_orden = float(rating or Decimal('0'))
            op_orden = float(opiniones_int or 0)
            fecha_orden = 0.0
            salida.append(CompetidorPlace(
                nombre=r.get('name') or '',
                place_id=pid,
                rating=rating,
                numero_opiniones=opiniones_int,
                direccion=direccion,
                puntuacion_orden=(rating_orden, op_orden, fecha_orden),
            ))
        # 3 reglas de desempate: rating DESC -> numero_opiniones DESC -> antiguedad (aún no tenemos, por ahora 0)
        salida.sort(key=lambda c: c.puntuacion_orden, reverse=True)
        return salida[:max_resultados]

    # --------- calcular benchmark ---------
    @transaction.atomic
    def calcular_benchmark(self, local: Local) -> Benchmark:
        competidores = self.buscar_competencia(local, max_resultados=20)
        # incluir local actual si tiene rating
        detalles: Optional[GooglePlace] = None
        if local.google_place_id:
            try:
                detalles = self.client.get_place(local.google_place_id)
            except Exception as e:
                logger.warning('Error obteniendo place details Local %s: %s', local.id, e)
        local_rating = detalles.rating if detalles else None
        local_opiniones = detalles.numero_opiniones if detalles else None
        todos_puntuaciones: List[Decimal] = []
        if local_rating is not None:
            todos_puntuaciones.append(local_rating)
        for c in competidores:
            if c.rating is not None:
                todos_puntuaciones.append(c.rating)

        def percentil(data: List[Decimal], p: float) -> Decimal:
            if not data:
                return Decimal('0')
            if len(data) == 1:
                return data[0]
            ordenada = sorted(data)
            k = (len(ordenada) - 1) * (p / 100.0)
            f = int(k)
            c_idx = min(f + 1, len(ordenada) - 1)
            if f == c_idx:
                return ordenada[f]
            return (ordenada[f] + (ordenada[c_idx] - ordenada[f]) * Decimal(str(k - f))).quantize(Decimal('0.01'))

        promedio_rubro = (
            (sum(todos_puntuaciones) / Decimal(len(todos_puntuaciones))).quantize(Decimal('0.01'))
            if todos_puntuaciones else Decimal('0')
        )
        top25 = percentil(todos_puntuaciones, 75)
        bottom25 = percentil(todos_puntuaciones, 25)

        puntuacion_local = local_rating or Decimal('0')

        # posicion = orden en la lista combinada
        combinada = []
        if local_rating is not None:
            combinada.append({
                'es_local': True,
                'rating': local_rating,
                'opiniones': local_opiniones or 0,
            })
        for c in competidores:
            combinada.append({
                'es_local': False,
                'rating': c.rating or Decimal('0'),
                'opiniones': c.numero_opiniones or 0,
            })
        combinada.sort(key=lambda x: (float(x['rating']), float(x['opiniones'])), reverse=True)
        posicion = 0
        for i, item in enumerate(combinada):
            if item['es_local']:
                posicion = i + 1
                break
        if posicion == 0 and combinada:
            posicion = len(combinada)

        datos_bench = {
            'competidores': [
                {
                    'nombre': c.nombre,
                    'place_id': c.place_id,
                    'rating': float(c.rating) if c.rating is not None else None,
                    'opiniones': c.numero_opiniones,
                    'direccion': c.direccion,
                } for c in competidores
            ],
            'percentiles': {
                'p25': float(bottom25),
                'p50': float(percentil(todos_puntuaciones, 50)),
                'p75': float(top25),
            },
            'local_rating': float(puntuacion_local) if puntuacion_local is not None else None,
            'local_opiniones': local_opiniones,
            'place_id': local.google_place_id,
        }

        return Benchmark.objects.create(
            local=local,
            posicion_local=posicion,
            total_evaluados=max(len(combinada), 1),
            puntuacion_local=puntuacion_local,
            puntuacion_promedio_rubro=promedio_rubro,
            top25_promedio=top25,
            bottom25_promedio=bottom25,
            datos=datos_bench,
        )

    # --------- sync por local ---------
    def sincronizar_local(self, local: Local) -> SyncLocalResult:
        pid = None
        rating_sync_ok = False
        nuevas = actualizadas = skip = 0
        error: Optional[str] = None
        try:
            pid = self._resolver_place_id(local)
            if not pid:
                error = 'No se pudo resolver google_place_id para este local.'
            else:
                detalles = self.client.get_place(pid)
                if detalles is None:
                    error = f'Google devolvió place vacío para place_id={pid}'
                else:
                    # actualizar datos geo local si están vacíos
                    updates = []
                    if not local.latitud and detalles.latitud:
                        local.latitud = detalles.latitud
                        updates.append('latitud')
                    if not local.longitud and detalles.longitud:
                        local.longitud = detalles.longitud
                        updates.append('longitud')
                    if not local.direccion and detalles.direccion:
                        local.direccion = detalles.direccion
                        updates.append('direccion')
                    if not local.ciudad and detalles.comuna:
                        local.ciudad = detalles.comuna
                        updates.append('ciudad')
                    if updates:
                        try:
                            local.save(update_fields=updates)
                        except Exception as e:
                            logger.warning('No se pudieron guardar datos geo Local %s: %s', local.id, e)
                    nuevas, actualizadas, skip = self._upsert_resenas(local, detalles.opiniones)
                    rating_sync_ok = True
            # benchmark incluso si no hay reseñas (para que exista ranking)
            try:
                self.calcular_benchmark(local)
            except Exception as e:
                logger.warning('Error calculando benchmark Local %s: %s', local.id, e)
        except Exception as e:
            error = f'{type(e).__name__}: {e}'
            logger.exception('Error sincronizando Local %s', local.id)
        return SyncLocalResult(
            local_id=str(local.id),
            nombre=local.nombre,
            place_id_usado=pid,
            nuevas_resenas=nuevas,
            actualizadas_resenas=actualizadas,
            skip_duplicadas=skip,
            rating_sync_ok=rating_sync_ok,
            error=error,
        )

    def sincronizar_todos(self, locales_qs=None) -> List[SyncLocalResult]:
        if locales_qs is None:
            locales_qs = Local.objects.filter(estado=Local.EstadoChoices.ACTIVO)
        locales_qs = locales_qs.select_related('negocio', 'negocio__rubro', 'comuna')
        resultados: List[SyncLocalResult] = []
        for loc in locales_qs:
            resultados.append(self.sincronizar_local(loc))
        return resultados
