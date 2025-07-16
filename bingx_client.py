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
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def test_connection(self) -> bool:
        try:
            response = self._make_request('GET', '/openApi/swap/v2/user/balance')
            return response.get('code') == 0
        except Exception:
            return False

    def get_account_balance(self) -> dict:
        try:
            response = self._make_request('GET', '/openApi/swap/v2/user/balance')
            if response.get('code') == 0:
                balance_info = response['data'].get('balance', {})
                return {
                    'success': True,
                    'data': [{
                        'asset': balance_info.get('asset', 'USDT'),
                        'available': balance_info.get('availableMargin', '0')
                    }]
                }
            return {'success': False, 'error': f"Unexpected response: {response}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_symbol_info(self, symbol: str) -> dict:
        try:
            response = self._make_request('GET', '/openApi/swap/v2/market/getAllContracts')
            if response.get('code') == 0:
                symbol_info = next((s for s in response.get('data', []) if s.get('symbol') == symbol), None)
                return {'success': True, 'data': symbol_info}
            return {'success': False, 'error': response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def place_limit_order(self, symbol: str, side: str, quantity: float, entry_price: float,
                          tp_price: float, sl_price: float, group_id: str) -> dict:
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "positionSide": "BOTH",
                "type": "LIMIT",
                "price": str(entry_price),
                "quantity": str(quantity),
                "timeInForce": "GTC",
                "takeProfit": f'{{"type":"TAKE_PROFIT_MARKET","stopPrice":{tp_price},"price":{tp_price},"workingType":"MARK_PRICE"}}',
                "stopLoss": f'{{"type":"STOP_MARKET","stopPrice":{sl_price},"price":{sl_price},"workingType":"MARK_PRICE"}}',
                "groupId": group_id
            }

            response = self._make_request('POST', '/openApi/swap/v2/trade/order', params)

            if response.get('code') == 0:
                order_data = response.get('data', {})
                return {
                    'success': True,
                    'order_id': order_data.get('orderId'),
                    'status': order_data.get('status'),
                    'raw_response': response
                }
            return {'success': False, 'error': response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}