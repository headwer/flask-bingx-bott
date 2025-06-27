import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles TradingView webhook signals and executes trades"""

    def __init__(self):
        self.bingx_client = BingXClient()

    def execute_trade(self, action: str, ticker: str, quantity: float = None) -> dict:
        """
        Execute a trade based on webhook signal

        Args:
            action: 'BUY' or 'SELL'
            ticker: Trading pair (e.g., 'BTCUSDT' or 'BTC-USDT')
            quantity: Optional - calculated automatically from account balance
        """

        try:
            logger.info(f"Executing trade: {action} {ticker}")

            # Validar acción
            if action not in ['BUY', 'SELL']:
                return {'success': False, 'error': f"Invalid action: {action}"}

            # Normalizar símbolo (elimina guiones y mayúsculas)
            symbol = ticker.replace('-', '').replace('/', '').upper()
            logger.debug(f"Normalized symbol: {symbol}")

            # Verificar claves API
            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {'success': False, 'error': "API keys not configured."}

            # Verificar conexión a BingX
            if not self.bingx_client.test_connection():
                return {'success': False, 'error': "Failed to connect to BingX API."}

            # Obtener balance
            account_info = self.bingx_client.get_account_balance()
            if not account_info['success']:
                return {'success': False, 'error': f"Failed to fetch balance: {account_info.get('error')}"}

            data = account_info.get('data')
            if not isinstance(data, list):
                return {'success': False, 'error': "Invalid balance format (not list)."}

            usdt_balance = next((item for item in data if item.get('asset') == 'USDT'), None)
            if not usdt_balance or float(usdt_balance.get('available', 0)) <= 0:
                return {'success': False, 'error': "No USDT balance available to trade."}

            balance = float(usdt_balance['available'])
            quantity_calc = round(balance / 7, 6)
            final_quantity = quantity if quantity else quantity_calc
            logger.info(f"Balance: {balance}, using quantity: {final_quantity}")

            # Validar par
            symbol_info = self.bingx_client.get_symbol_info(symbol)
            if not symbol_info['success'] or symbol_info['data'] is None:
                return {'success': False, 'error': f"Invalid trading pair: {symbol}"}

            # Ejecutar orden de mercado
            result = self.bingx_client.place_market_order(
                symbol=symbol,
                side=action,
                quantity=final_quantity
            )

            if result['success']:
                logger.info(f"Order executed: {result}")
                return {
                    'success': True,
                    'order_id': result.get('order_id'),
                    'symbol': symbol,
                    'side': action,
                    'quantity': final_quantity,
                    'status': result.get('status'),
                    'message': f"{action} order executed for {final_quantity} {symbol}"
                }
            else:
                logger.error(f"Order failed: {result}")
                return {'success': False, 'error': result.get('error', 'Order failed')}

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {'success': False, 'error': f"Trade execution failed: {str(e)}"}

    def test_connection(self) -> bool:
        return self.bingx_client.test_connection()

    def get_account_info(self) -> dict:
        return self.bingx_client.get_account_balance()