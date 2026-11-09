import hmac
import hashlib
import json
import urllib.request
import urllib.parse
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('clientbeat')


class FlowService:
    """
    Servicio de integración con la Pasarela de Pagos Flow Chile (API v2).
    Soporta:
      - Pagos únicos (/payment/*)
      - Enrolamiento de tarjetas Oneclick / Clientes (/customer/*)
      - Gestión de Planes Recurrentes (/plans/*)
      - Creación y Ciclo de Vida de Suscripciones (/subscription/*)
      - Cobros automáticos adicionales (/customer/charge)
      - Modo Simulación/Mock cuando las llaves no están configuradas en el entorno.
    """

    def __init__(self):
        self.api_key = getattr(settings, 'FLOW_API_KEY', '')
        self.secret_key = getattr(settings, 'FLOW_SECRET_KEY', '')
        self.environment = getattr(settings, 'FLOW_ENVIRONMENT', 'sandbox')

        if self.environment == 'production':
            self.base_url = 'https://www.flow.cl/api'
        else:
            self.base_url = 'https://sandbox.flow.cl/api'

    @property
    def is_mock(self) -> bool:
        return not self.api_key or self.api_key.startswith('your_') or self.api_key == 'test'

    def firmar_parametros(self, params: Dict[str, Any]) -> str:
        """Calcula la firma HMAC-SHA256 ordenando alfabéticamente las llaves."""
        keys_ordenadas = sorted(params.keys())
        cadena = "".join([f"{k}{params[k]}" for k in keys_ordenadas if params[k] is not None])
        firma = hmac.new(
            self.secret_key.encode('utf-8'),
            cadena.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return firma

    def validar_firma_webhook(
        self,
        params: Dict[str, Any],
        header_signature: Optional[str] = None,
        raw_body: Optional[bytes] = None
    ) -> bool:
        """
        Verifica la firma criptográfica HMAC-SHA256 de un webhook entrante de Flow.
        - Si viene parámetro 's' en el formulario/JSON, valida contra los demás parámetros ordenados.
        - Si viene cabecera 'X-Flow-Signature', valida el cuerpo crudo con FLOW_WEBHOOK_SECRET o FLOW_SECRET_KEY.
        - Si no trae firma (ej. notificación simple de token que luego se valida vía GET /payment/getStatus firmada),
          retorna True tras validar contra el servidor de Flow.
        """
        if self.is_mock or not self.secret_key:
            return True

        if 's' in params:
            copia = {k: v for k, v in params.items() if k != 's'}
            firma_esperada = self.firmar_parametros(copia)
            return hmac.compare_digest(str(params['s']), firma_esperada)

        if header_signature and raw_body:
            webhook_secret = getattr(settings, 'FLOW_WEBHOOK_SECRET', '')
            if not webhook_secret or webhook_secret.startswith('your_'):
                webhook_secret = self.secret_key
            firma_body = hmac.new(
                webhook_secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(header_signature.strip(), firma_body)

        return True

    def _request_post(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una petición POST a la API de Flow con firma digital."""
        params['apiKey'] = self.api_key
        params['s'] = self.firmar_parametros(params)

        try:
            encoded_data = urllib.parse.urlencode(params).encode('utf-8')
            req = urllib.request.Request(f"{self.base_url}{endpoint}", data=encoded_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=12) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
            except Exception:
                error_body = {'message': str(e)}
            logger.error("[FlowService HTTPError POST %s]: %s (code %s)", endpoint, error_body, e.code)
            return {'error': error_body.get('message', str(e)), 'code': e.code, 'is_mock': False}
        except Exception as e:
            logger.exception("[FlowService Exception POST %s]: %s", endpoint, e)
            return {'error': str(e), 'is_mock': False}

    def _request_get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una petición GET a la API de Flow con firma digital."""
        params['apiKey'] = self.api_key
        params['s'] = self.firmar_parametros(params)

        try:
            url = f"{self.base_url}{endpoint}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=12) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
            except Exception:
                error_body = {'message': str(e)}
            logger.error("[FlowService HTTPError GET %s]: %s (code %s)", endpoint, error_body, e.code)
            return {'error': error_body.get('message', str(e)), 'code': e.code, 'is_mock': False}
        except Exception as e:
            logger.exception("[FlowService Exception GET %s]: %s", endpoint, e)
            return {'error': str(e), 'is_mock': False}

    # =========================================================================
    # 1. CLIENTES FLOW (CUSTOMERS)
    # =========================================================================
    def crear_cliente(self, nombre: str, email: str, external_id: str) -> Dict[str, Any]:
        """Crea un cliente en Flow o devuelve su información."""
        if self.is_mock:
            return {
                'customerId': f"MOCK_CUS_{external_id[:8]}",
                'name': nombre,
                'email': email,
                'externalId': external_id,
                'status': 1,
                'is_mock': True
            }

        params = {
            'name': nombre[:100],
            'email': email,
            'externalId': str(external_id)[:50],
        }
        return self._request_post('/customer/create', params)

    def obtener_cliente(self, customer_id: str) -> Dict[str, Any]:
        """Obtiene el detalle de un cliente en Flow."""
        if self.is_mock or customer_id.startswith('MOCK_'):
            return {'customerId': customer_id, 'status': 1, 'is_mock': True}
        return self._request_get('/customer/get', {'customerId': customer_id})

    # =========================================================================
    # 2. ENROLAMIENTO DE TARJETA (ONECLICK / PATPASS)
    # =========================================================================
    def iniciar_registro_tarjeta(self, customer_id: str, url_retorno: str) -> Dict[str, Any]:
        """
        Genera la URL de Flow para que el cliente ingrese su tarjeta de crédito/débito.
        """
        if self.is_mock or customer_id.startswith('MOCK_'):
            logger.info("[FlowService Mock] Enrolamiento simulado de tarjeta para cliente %s", customer_id)
            token = f"MOCK_CARD_REG_{customer_id[:8]}"
            return {
                'url': f"{url_retorno}?token={token}",
                'token': token,
                'is_mock': True
            }

        params = {
            'customerId': customer_id,
            'url_return': url_retorno,
        }
        resp = self._request_post('/customer/register', params)
        if 'url' in resp and 'token' in resp:
            full_url = f"{resp['url']}?token={resp['token']}"
            return {
                'url': full_url,
                'token': resp['token'],
                'is_mock': False
            }
        return resp

    def obtener_estado_registro_tarjeta(self, token: str) -> Dict[str, Any]:
        """
        Consulta el estado del registro de la tarjeta dado el token retornado por Flow.
        Estado 1 = Registrada con éxito, 0 = Pendiente, 2 = Rechazada.
        """
        if self.is_mock or token.startswith('MOCK_CARD_REG_'):
            return {
                'status': 1,
                'status_str': 'REGISTRADA',
                'customerId': 'MOCK_CUS_DEV',
                'creditCardType': 'Visa',
                'last4CardDigits': '4242',
                'is_mock': True
            }

        data = self._request_get('/customer/getRegisterStatus', {'token': token})
        status_code = data.get('status')
        status_map = {0: 'PENDIENTE', 1: 'REGISTRADA', 2: 'RECHAZADA'}
        data['status_str'] = status_map.get(status_code, 'DESCONOCIDO')
        return data

    # =========================================================================
    # 3. PLANES RECURRENTES EN FLOW
    # =========================================================================
    def sincronizar_o_crear_plan(
        self,
        plan_id: str,
        nombre: str,
        monto_clp: int,
        intervalo: int = 3, # 1: diario, 2: semanal, 3: mensual, 4: anual
        trial_period_days: int = 0,
        url_callback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crea o sincroniza un plan mensual en Flow con el monto exacto de ClientBeat
        y registra automáticamente la urlCallback del Webhook (/billing/flow/webhook/).
        Si el plan ya existe, lo retorna (actualizando monto y urlCallback si cambiaron).
        """
        domain = getattr(settings, 'SITE_DOMAIN', 'https://www.clientbeat.cl').rstrip('/')
        callback_url = url_callback or f"{domain}/billing/flow/webhook/"

        if self.is_mock:
            return {
                'planId': plan_id,
                'name': nombre,
                'amount': monto_clp,
                'interval': intervalo,
                'urlCallback': callback_url,
                'is_mock': True
            }

        # Verificar si ya existe
        plan_existente = self._request_get('/plans/get', {'planId': plan_id})
        if 'planId' in plan_existente and not plan_existente.get('error'):
            # Si el monto o el urlCallback cambiaron y el plan lo permite, actualizamos
            monto_actual = int(float(plan_existente.get('amount') or 0))
            callback_actual = plan_existente.get('urlCallback') or ''
            if monto_actual != int(monto_clp) or callback_actual != callback_url:
                edit_params = {
                    'planId': plan_id,
                    'name': nombre[:100],
                    'amount': str(int(monto_clp)),
                    'urlCallback': callback_url,
                }
                self._request_post('/plans/edit', edit_params)
            return plan_existente

        params = {
            'planId': plan_id[:50],
            'name': nombre[:100],
            'currency': 'CLP',
            'amount': str(int(monto_clp)),
            'interval': str(intervalo),
            'interval_count': '1',
            'trial_period_days': str(int(trial_period_days)),
            'urlCallback': callback_url,
        }
        return self._request_post('/plans/create', params)

    # =========================================================================
    # 4. SUSCRIPCIONES (FLOW SUBSCRIPTION ENGINE)
    # =========================================================================
    def crear_suscripcion(
        self,
        customer_id: str,
        plan_id: str,
        trial_period_days: int = 0,
        subscription_start: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Vincula un cliente con un plan en Flow para activar cobros automáticos periódicos.
        """
        if self.is_mock or customer_id.startswith('MOCK_'):
            return {
                'subscriptionId': f"MOCK_SUB_{customer_id[:6]}_{plan_id[:6]}",
                'status': 1, # 1 = Activa
                'status_str': 'ACTIVA',
                'customerId': customer_id,
                'planId': plan_id,
                'is_mock': True
            }

        params = {
            'customerId': customer_id,
            'planId': plan_id,
        }
        if trial_period_days > 0:
            params['trial_period_days'] = str(trial_period_days)
        if subscription_start:
            params['subscription_start'] = subscription_start

        resp = self._request_post('/subscription/create', params)
        status_code = resp.get('status')
        status_map = {0: 'PENDIENTE', 1: 'ACTIVA', 2: 'TRIAL', 3: 'VENCIDA', 4: 'CANCELADA'}
        resp['status_str'] = status_map.get(status_code, 'DESCONOCIDO')
        return resp

    def modificar_plan_suscripcion(self, subscription_id: str, nuevo_plan_id: str) -> Dict[str, Any]:
        """Modifica el plan al que apunta una suscripción existente en Flow."""
        if self.is_mock or subscription_id.startswith('MOCK_'):
            return {'subscriptionId': subscription_id, 'planId': nuevo_plan_id, 'status': 1, 'is_mock': True}

        params = {
            'subscriptionId': subscription_id,
            'planId': nuevo_plan_id,
        }
        return self._request_post('/subscription/edit', params)

    def cancelar_suscripcion(self, subscription_id: str, at_period_end: int = 1) -> Dict[str, Any]:
        """Cancela una suscripción en Flow (1 = al término del ciclo actual)."""
        if self.is_mock or subscription_id.startswith('MOCK_'):
            return {'subscriptionId': subscription_id, 'status': 4, 'status_str': 'CANCELADA', 'is_mock': True}

        params = {
            'subscriptionId': subscription_id,
            'at_period_end': str(at_period_end),
        }
        return self._request_post('/subscription/cancel', params)

    def obtener_suscripcion(self, subscription_id: str) -> Dict[str, Any]:
        """Consulta el estado de una suscripción en Flow."""
        if self.is_mock or subscription_id.startswith('MOCK_'):
            return {'subscriptionId': subscription_id, 'status': 1, 'status_str': 'ACTIVA', 'is_mock': True}

        data = self._request_get('/subscription/get', {'subscriptionId': subscription_id})
        status_code = data.get('status')
        status_map = {0: 'PENDIENTE', 1: 'ACTIVA', 2: 'TRIAL', 3: 'VENCIDA', 4: 'CANCELADA'}
        data['status_str'] = status_map.get(status_code, 'DESCONOCIDO')
        return data

    # =========================================================================
    # 5. COBRO DIRECTO / CARGO ADICIONAL (/customer/charge)
    # =========================================================================
    def cobrar_cargo_adicional(
        self,
        customer_id: str,
        monto: int,
        concepto: str
    ) -> Dict[str, Any]:
        """
        Cobra inmediatamente a la tarjeta enrolada del cliente sin pasar por pasarela interactiva.
        Ideal para el cobro proporcional de sucursales agregadas a mitad de mes.
        """
        if self.is_mock or customer_id.startswith('MOCK_'):
            return {
                'status': 2, # 2 = Pagado
                'status_str': 'PAGADO',
                'amount': monto,
                'flowOrder': 999123,
                'is_mock': True
            }

        params = {
            'customerId': customer_id,
            'amount': str(int(monto)),
            'currency': 'CLP',
            'subject': concepto[:200],
        }
        return self._request_post('/customer/charge', params)

    # =========================================================================
    # 6. PAGO ÚNICO LEGACY (/payment/create)
    # =========================================================================
    def crear_orden_pago(
        self,
        orden_compra: str,
        monto: int,
        concepto: str,
        email_pagador: str,
        url_retorno: str,
        url_confirmacion: str,
    ) -> Dict[str, Any]:
        """Crea una orden de pago transaccional en Flow (fallback)."""
        if self.is_mock:
            logger.info("[FlowService Mock] Generando orden de pago simulada para %s ($%s CLP)", orden_compra, monto)
            return {
                'url': f"{url_retorno}?token=MOCK_FLOW_TOKEN_{orden_compra}&status=1",
                'token': f"MOCK_FLOW_TOKEN_{orden_compra}",
                'flowOrder': 999999,
                'is_mock': True
            }

        params = {
            'commerceOrder': orden_compra,
            'subject': concepto[:200],
            'currency': 'CLP',
            'amount': str(int(monto)),
            'email': email_pagador,
            'urlConfirmation': url_confirmacion,
            'urlReturn': url_retorno,
        }
        resp = self._request_post('/payment/create', params)
        if 'url' in resp and 'token' in resp:
            full_url = f"{resp['url']}?token={resp['token']}"
            return {
                'url': full_url,
                'token': resp['token'],
                'flowOrder': resp.get('flowOrder'),
                'is_mock': False
            }
        return resp

    def obtener_estado_pago(self, token: str) -> Dict[str, Any]:
        """Consulta el estado de un pago dado su token."""
        if self.is_mock or token.startswith('MOCK_FLOW_TOKEN_'):
            return {
                'status': 2,
                'status_str': 'PAGADO',
                'amount': 25000,
                'payer': 'demo@clientbeat.cl',
                'is_mock': True
            }

        data = self._request_get('/payment/getStatus', {'token': token})
        status_code = data.get('status')
        status_map = {1: 'PENDIENTE', 2: 'PAGADO', 3: 'RECHAZADO', 4: 'ANULADO'}
        data['status_str'] = status_map.get(status_code, 'DESCONOCIDO')
        return data
