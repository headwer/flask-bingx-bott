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
        """Create HMAC-SHA256 signature."""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Send signed request to BingX API."""
        if params is None:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        query = urlencode(params)
        params['signature'] = self._generate_signature(query)
        headers = {
            'X-BX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10) if method.upper() == 'GET' else requests.post(url, params=params, headers=headers, timeout=10)
            logger.debug(f"Request {method} {url} → {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Check API key and connection validity."""
        try:
            if not self.api_key or not self.secret_key:
                return False
            resp = self._make_request('GET', '/openApi/swap/v2/user/balance')
            return resp.get('code') == 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_account_balance(self) -> dict:
        """Retrieve USDT balance."""
        try:
            resp = self._make_request('GET', '/openApi/swap/v2/user/balance')
            logger.debug(f"Balance response: {resp}")
            if resp.get('code') == 0 and 'data' in resp:
                bal = resp['data'].get('balance', {})
                return {'success': True, 'data': [{'asset': bal.get('asset', 'USDT'), 'available': bal.get('availableMargin', '0')}]}
            return {'success': False, 'error': f"Unexpected response: {resp}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        """
        Place a market order.
        
        :param symbol: e.g. "BTC-USDT"
        :param side: "BUY" or "SELL"
        :param quantity: e.g. 0.001 (float)
        """
        try:
            position = "LONG" if side == "BUY" else "SHORT"
            qty_str = f"{quantity:.4f}"  # e.g. "0.1234"
            params = {
                'symbol': symbol,
                'side': side,
                'positionSide': position,
                'type': 'MARKET',
                'quantity': qty_str
            }
            logger.info(f"Posting order: {side} {qty_str} {symbol} ({position})")
            resp = self._make_request('POST', '/openApi/swap/v2/trade/order', params)
            if resp.get('code') == 0:
                od = resp.get('data', {})
                return {
                    'success': True,
                    'order_id': od.get('orderId'),
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'status': od.get('status'),
                    'raw_response': resp
                }
            else:
                em = resp.get('msg', 'Unknown error')
                logger.error(f"Order error: {em}")
                return {'success': False, 'error': f"BingX API error: {em}", 'raw_response': resp}
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {'success': False, 'error': f"Order execution failed: {e}"}