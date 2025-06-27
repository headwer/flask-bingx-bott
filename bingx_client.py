import time
import hmac
import hashlib
import requests
import logging

logger = logging.getLogger(__name__)

class BingXClient:
    BASE_URL = "https://open-api.bingx.com"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_timestamp(self):
        return str(int(time.time() * 1000))

    def _sign(self, params):
        query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
        signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _make_request(self, method, endpoint, params=None):
        if params is None:
            params = {}
        params['timestamp'] = self._get_timestamp()
        signature = self._sign(params)
        params['signature'] = signature
        headers = {
            'X-BX-APIKEY': self.api_key
        }

        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=headers, params=params)
        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {}

    def get_account_balance(self) -> dict:
        """Get futures account balance"""
        try:
            response = self._make_request('GET', '/openApi/swap/v2/user/balance')
            logger.debug(f"Raw balance response: {response}")

            if response.get('code') == 0 and 'data' in response and 'balance' in response['data']:
                balance_data = response['data']['balance']
                return {
                    'success': True,
                    'data': [balance_data]  # 🔁 Convertido a lista para evitar errores
                }
            else:
                return {
                    'success': False,
                    'error': "Invalid balance structure from API."
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def place_order(self, symbol: str, side: str, quantity: float, price: float = None):
        """Place a futures order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'positionSide': 'BOTH',
                'type': 'MARKET',
                'quantity': quantity
            }
            response = self._make_request('POST', '/openApi/swap/v2/trade/order', params)
            logger.debug(f"Raw order response: {response}")

            if response.get('code') == 0:
                return {
                    'success': True,
                    'data': response.get('data')
                }
            else:
                return {
                    'success': False,
                    'error': response.get('msg', 'Unknown error')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_symbol_info(self):
        """Get list of available trading symbols"""
        try:
            response = self._make_request('GET', '/openApi/swap/v2/market/getAllContracts')
            logger.debug(f"Raw symbol list response: {response}")

            if response.get('code') == 0 and 'data' in response:
                return {
                    'success': True,
                    'data': response.get('data')
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to fetch symbol info"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }