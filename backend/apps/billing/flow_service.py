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
    Soporta firmas HMAC-SHA256, llamadas a Sandbox/Producción y modo Simulación/Mock
    cuando las llaves no están configuradas en el entorno.
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
        """
        Calcula la firma HMAC-SHA256 ordenando alfabéticamente las llaves.
        """
        keys_ordenadas = sorted(params.keys())
        cadena = "".join([f"{k}{params[k]}" for k in keys_ordenadas])
        firma = hmac.new(
            self.secret_key.encode('utf-8'),
            cadena.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return firma

    def crear_orden_pago(
        self,
        orden_compra: str,
        monto: int,
        concepto: str,
        email_pagador: str,
        url_retorno: str,
        url_confirmacion: str,
    ) -> Dict[str, Any]:
        """
        Crea una orden de pago en Flow. Si está en modo mock, retorna una URL de simulación.
        """
        if self.is_mock:
            logger.info("[FlowService Mock] Generando orden de pago simulada para %s ($%s CLP)", orden_compra, monto)
            return {
                'url': f"{url_retorno}?token=MOCK_FLOW_TOKEN_{orden_compra}&status=1",
                'token': f"MOCK_FLOW_TOKEN_{orden_compra}",
                'flowOrder': 999999,
                'is_mock': True
            }

        params = {
            'apiKey': self.api_key,
            'commerceOrder': orden_compra,
            'subject': concepto[:200],
            'currency': 'CLP',
            'amount': str(int(monto)),
            'email': email_pagador,
            'urlConfirmation': url_confirmacion,
            'urlReturn': url_retorno,
        }
        params['s'] = self.firmar_parametros(params)

        try:
            encoded_data = urllib.parse.urlencode(params).encode('utf-8')
            req = urllib.request.Request(f"{self.base_url}/payment/create", data=encoded_data, method='POST')
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                if 'url' in resp_data:
                    full_url = f"{resp_data['url']}?token={resp_data['token']}"
                    return {
                        'url': full_url,
                        'token': resp_data['token'],
                        'flowOrder': resp_data.get('flowOrder'),
                        'is_mock': False
                    }
                logger.error("[FlowService Error] Fallo al crear orden de pago: %s", resp_data)
                return {'error': resp_data.get('message', 'Error en pasarela Flow'), 'is_mock': False}
        except Exception as e:
            logger.exception("[FlowService Exception] Error conectando con Flow: %s", e)
            return {'error': str(e), 'is_mock': False}

    def obtener_estado_pago(self, token: str) -> Dict[str, Any]:
        """
        Consulta el estado de un pago dado su token.
        """
        if self.is_mock or token.startswith('MOCK_FLOW_TOKEN_'):
            return {
                'status': 2, # 2 = Pagado en Flow
                'status_str': 'PAGADO',
                'amount': 25000,
                'payer': 'demo@clientbeat.cl',
                'is_mock': True
            }

        params = {
            'apiKey': self.api_key,
            'token': token,
        }
        params['s'] = self.firmar_parametros(params)

        try:
            url = f"{self.base_url}/payment/getStatus?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                status_code = data.get('status')
                status_map = {1: 'PENDIENTE', 2: 'PAGADO', 3: 'RECHAZADO', 4: 'ANULADO'}
                data['status_str'] = status_map.get(status_code, 'DESCONOCIDO')
                return data
        except Exception as e:
            logger.exception("[FlowService Exception] Error al obtener estado de token %s: %s", token, e)
            return {'error': str(e), 'status_str': 'ERROR'}
