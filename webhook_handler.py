import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self):
        self.bingx_client = BingXClient()

    def execute_trade(self, action: str, ticker: str, quantity: float = None) -> dict:
        try:
            logger.info(f"Executing trade: {action} {ticker}")

            if action not in ['BUY', 'SELL']:
                return {'success': False, 'error': f"Invalid action: {action}"}

            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {'success': False, 'error': "API keys not configured."}

            if not self.bingx_client.test_connection():
                return {'success': False, 'error': "Failed to connect to BingX API."}

            account_info = self.bingx_client.get_account_balance()
            if not account_info['success']:
                return {'success': False, 'error': f"Failed to fetch balance: {account_info.get('error', '')}"}

            data = account_info.get('data')
            if not isinstance(data, list):
                return {'success': False, 'error': "Invalid balance format"}

            usdt_balance = next((item for item in data if item.get('asset') == 'USDT'), None)
            if not usdt_balance or float(usdt_balance.get('availableMargin', 0)) <= 0:
                return {'success': False, 'error': "No USDT balance available to trade."}

            balance = float(usdt_balance['availableMargin'])
            quantity = round(balance / 7, 6)
            logger.info(f"Available USDT balance: {balance} -> Trading quantity: {quantity}")

            # Saltamos la validación del símbolo
            result = self.bingx_client.place_market_order(
                symbol=ticker,
                side=action,
                quantity=quantity
            )

            if result['success']:
                logger.info(f"Trade executed: {result}")
                return {
                    'success': True,
                    'order_id': result.get('order_id'),
                    'symbol': ticker,
                    'side': action,
                    'quantity': quantity,
                    'status': result.get('status'),
                    'message': f"Executed {action} order for {quantity} {ticker}"
                }
            else:
                logger.error(f"Trade failed: {result}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }

        except Exception as e:
            logger.error(f"Trade error: {str(e)}")
            return {
                'success': False,
                'error': f"Trade execution failed: {str(e)}"
            }

    def test_connection(self) -> bool:
        return self.bingx_client.test_connection()

    def get_account_info(self) -> dict:
        return self.bingx_client.get_account_balance()