import os
import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class BingXClient:
    def __init__(self):
        self.api_key = os.getenv("BINGX_API_KEY", "")
        self.secret_key = os.getenv("BINGX_SECRET_KEY", "")
        self.base_url = "https://open-api.bingx.com"

        if not self.api_key or not self.secret_key:
            logger.warning("BingX API credentials not found in environment variables")

    def _generate_signature(self, params: str) -> str:
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        if not params:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        params['signature'] = signature

        headers = {
            'X-BX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"BingX API request: {method} {url}")
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"BingX API request failed: {str(e)}")
            raise

    def test_connection(self) -> bool:
        try:
            if not self.api_key or not self.secret_key:
                return False
            response = self._make_request('GET', '/openApi/swap/v2/user/balance')
            return response.get('code') == 0
        except Exception as e:
            logger.error(f"BingX connection test failed: {str(e)}")
            return False

    def get_account_balance(self) -> dict:
        try:
            response = self._make_request('GET', '/openApi/swap/v2/user/balance')
            raw_data = response.get('data', {})

            logger.debug(f"Raw balance response: {raw_data}")

            if isinstance(raw_data, list):
                return {'success': True, 'data': raw_data}
            elif isinstance(raw_data, dict) and 'balance' in raw_data:
                return {'success': True, 'data': [raw_data['balance']]}
            else:
                return {'success': False, 'error': "Invalid response format: expected a list of balances"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            response = self._make_request('GET', '/openApi/swap/v2/market/getAllContracts')
            if response.get('code') == 0:
                contracts = response.get('data', [])
                symbol_info = next((c for c in contracts if c.get('symbol') == symbol), None)
                return {'success': True, 'data': symbol_info} if symbol_info else {
                    'success': False,
                    'error': f"Symbol {symbol} not found"
                }
            else:
                return {
                    'success': False,
                    'error': response.get('msg', 'API error fetching symbols')
                }
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

            logger.info(f"Placing {side} market order: {quantity} {symbol}")
            response = self._make_request('POST', '/openApi/swap/v2/trade/order', params)

            if response.get('code') == 0:
                order_data = response.get('data', {})
                return {
                    'success': True,
                    'order_id': order_data.get('orderId'),
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'status': order_data.get('status'),
                    'raw_response': response
                }
            else:
                return {
                    'success': False,
                    'error': response.get('msg', 'Unknown error'),
                    'raw_response': response
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Order execution failed: {str(e)}"
            }