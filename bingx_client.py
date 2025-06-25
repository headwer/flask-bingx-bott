import os
import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class BingXClient:
    """BingX API client for executing trades"""
    
    def __init__(self):
        self.api_key = os.getenv("BINGX_API_KEY", "")
        self.secret_key = os.getenv("BINGX_SECRET_KEY", "")
        self.base_url = "https://open-api.bingx.com"
        
        if not self.api_key or not self.secret_key:
            logger.warning("BingX API credentials not found in environment variables")
    
    def _generate_signature(self, params: str) -> str:
        """Generate HMAC-SHA256 signature for BingX API"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Make authenticated request to BingX API"""
        if not params:
            params = {}
        
        # Add timestamp
        params['timestamp'] = int(time.time() * 1000)
        
        # Create query string
        query_string = urlencode(params)
        
        # Generate signature
        signature = self._generate_signature(query_string)
        params['signature'] = signature
        
        # Headers
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
        """Test connection to BingX API"""
        try:
            if not self.api_key or not self.secret_key:
                return False
            
            # Test with account info endpoint
            response = self._make_request('GET', '/openApi/spot/v1/account/balance')
            return response.get('code') == 0
            
        except Exception as e:
            logger.error(f"BingX connection test failed: {str(e)}")
            return False
    
    def get_account_balance(self) -> dict:
        """Get account balance"""
        try:
            response = self._make_request('GET', '/openApi/spot/v1/account/balance')
            return {
                'success': True,
                'data': response.get('data', [])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        """
        Place a market order on BingX
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
        """
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': str(quantity)
            }
            
            logger.info(f"Placing {side} market order: {quantity} {symbol}")
            
            response = self._make_request('POST', '/openApi/spot/v1/trade/order', params)
            
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
                error_msg = response.get('msg', 'Unknown error')
                logger.error(f"BingX order failed: {error_msg}")
                return {
                    'success': False,
                    'error': f"BingX API error: {error_msg}",
                    'raw_response': response
                }
                
        except Exception as e:
            logger.error(f"Failed to place market order: {str(e)}")
            return {
                'success': False,
                'error': f"Order execution failed: {str(e)}"
            }
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol information"""
        try:
            params = {'symbol': symbol}
            response = self._make_request('GET', '/openApi/spot/v1/common/symbols', params)
            
            if response.get('code') == 0:
                symbols = response.get('data', {}).get('symbols', [])
                symbol_info = next((s for s in symbols if s.get('symbol') == symbol), None)
                
                return {
                    'success': True,
                    'data': symbol_info
                }
            else:
                return {
                    'success': False,
                    'error': response.get('msg', 'Symbol not found')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
