import os
import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class BingXClient:
    """BingX Futures API client for executing trades"""

    def __init__(self):
        self.api_key = os.getenv("BINGX_API_KEY", "")
        self.secret_key = os.getenv("BINGX_SECRET_KEY", "")
        self.base_url = "https://open-api.bingx.com"
        if not self.api_key or not self.secret_key:
            logger.warning("BingX API credentials not found in environment variables")

    def _generate_signature(self, params: str) -> str:
        return hmac.new(self.secret_key.encode(), params.encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        if not params:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        query_string = urlencode(params)
        params['signature'] = self._generate_signature(query_string)
        headers = {
            'X-BX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                resp = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                resp = requests.post(url, params=params, headers=headers, timeout=10)
            logger.debug(f"BingX API request: {method} {url}")
            logger.debug(f"Response: {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"BingX API request failed: {e}")
            raise

    def test_connection(self) -> bool:
        try:
            if not self.api_key or not self.secret_key:
                return False
            resp = self._make_request('GET', '/openApi/swap/v2/user/balance')
            return resp.get('code') == 0
        except:
            return False

    def get_account_balance(self) -> dict:
        try:
            resp = self._make_request('GET', '/openApi/swap/v2/user/balance')
            logger.debug(f"Balance raw: {resp}")
            if resp.get('code') == 0:
                balance_info = resp.get('data', {}).get('balance', {})
                if balance_info.get('asset') == 'USDT':
                    return {'success': True, 'data': {'balance': balance_info}}
            return {'success': False, 'error': resp.get('msg', 'No USDT balance')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'positionSide': 'BOTH',
                'type': 'MARKET',
                'quantity': str(quantity)
            }
            resp = self._make_request('POST', '/openApi/swap/v2/trade/order', params)
            if resp.get('code') == 0:
                data = resp.get('data', {})
                return {'success': True, 'order_id': data.get('orderId'), 'symbol': symbol, 'side': side, 'quantity': quantity, 'status': data.get('status')}
            msg = resp.get('msg', 'Error')
            return {'success': False, 'error': f"BingX API error: {msg}"}
        except Exception as e:
            return {'success': False, 'error': f"Order execution failed: {e}"}

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            resp = self._make_request('GET', '/openApi/swap/v2/market/getAllContracts')
            if resp.get('code') == 0:
                for s in resp.get('data', []):
                    if s.get('symbol') == symbol:
                        return {'success': True, 'data': s}
                return {'success': False, 'error': 'Symbol not found'}
            return {'success': False, 'error': resp.get('msg', 'Failed to fetch symbols')}
        except Exception as e:
            return {'success': False, 'error': str(e)}