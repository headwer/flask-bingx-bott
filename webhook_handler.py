import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self):
        self.bingx_client = BingXClient()

    def execute_trade(self, action: str, ticker: str, quantity: float = None) -> dict:
        try:
            ticker = ticker.upper()  # convierte a mayúsculas pero conserva guion
            logger.info(f"Executing trade: {action} {ticker}")

            if action not in ['BUY', 'SELL']:
                return {'success': False, 'error': f"Invalid action: {action}"}

            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {'success': False, 'error': "API keys not configured."}

            if not self.bingx_client.test_connection():
                return {'success': False, 'error': "Failed to connect to BingX API."}

            acc = self.bingx_client.get_account_balance()
            if not acc['success']:
                return {'success': False, 'error': f"Failed to fetch balance: {acc.get('error')}"}
            data = acc['data']
            if not isinstance(data, list):
                return {'success': False, 'error': "Invalid balance format"}

            usdt = next((i for i in data if i.get('asset')=='USDT'), None)
            if not usdt or float(usdt.get('available',0)) <= 0:
                return {'success': False, 'error': "No USDT balance available."}

            balance = float(usdt['available'])
            quantity = balance / 7
            rounded = round(quantity,6)

            logger.warning("⚠️ *Validación de símbolo parcialmente desactivada para pruebas*")
            # --> Intentamos ejecutar la orden sin validar símbolo

            result = self.bingx_client.place_market_order(
                symbol=ticker,
                side=action,
                quantity=rounded
            )

            if result.get('success'):
                return {
                    'success': True,
                    'order_id': result.get('order_id'),
                    'symbol': ticker,
                    'side': action,
                    'quantity': rounded,
                    'status': result.get('status'),
                    'message': f"Executed {action} on {ticker}"
                }
            else:
                return {'success': False, 'error': result.get('error')}

        except Exception as e:
            logger.error(f"Trade error: {e}")
            return {'success': False, 'error': f"Trade execution failed: {e}"}

    def test_connection(self) -> bool:
        return self.bingx_client.test_connection()

    def get_account_info(self) -> dict:
        return self.bingx_client.get_account_balance()