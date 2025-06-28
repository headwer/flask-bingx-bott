import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles TradingView webhook signals and executes trades"""

    def __init__(self):
        self.bingx_client = BingXClient()

    def execute_trade(self, message: str) -> dict:
        """
        Execute a trade based on webhook signal message.

        Expected message format: "TICKER|ACTION"
        Example: "BTC-USDT|LONG", "BTC-USDT|CLOSE_SHORT"

        Args:
            message: string with ticker and action separated by '|'
        """

        try:
            logger.info(f"Received webhook message: {message}")

            if '|' not in message:
                return {'success': False, 'error': 'Invalid message format'}

            ticker, action = message.split('|')
            ticker = ticker.strip()
            action = action.strip().upper()

            logger.info(f"Parsed ticker: {ticker}, action: {action}")

            # Check API keys
            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {
                    'success': False,
                    'error': "API keys not configured."
                }

            # Test connection
            if not self.bingx_client.test_connection():
                return {
                    'success': False,
                    'error': "Failed to connect to BingX API."
                }

            # Handle close actions
            if action == 'CLOSE_LONG':
                return self.bingx_client.close_position(symbol=ticker, side='LONG')
            elif action == 'CLOSE_SHORT':
                return self.bingx_client.close_position(symbol=ticker, side='SHORT')

            # Validate symbol info
            symbol_info = self.bingx_client.get_symbol_info(ticker)
            if not symbol_info['success'] or symbol_info['data'] is None:
                return {
                    'success': False,
                    'error': f"Invalid trading pair: {ticker}. {symbol_info.get('error', '')}"
                }

            # Get account balance
            account_info = self.bingx_client.get_account_balance()
            data = account_info.get('data', [])

            usdt_balance = next((item for item in data if item.get('asset') == 'USDT'), None)
            if not usdt_balance:
                return {
                    'success': False,
                    'error': "No USDT balance found."
                }

            balance = float(usdt_balance['available'])
            quantity = balance / 7  # As per your previous logic
            rounded_quantity = round(quantity, 6)

            # Place orders based on action
            if action == 'LONG':
                return self.bingx_client.place_market_order(ticker, 'BUY', rounded_quantity)
            elif action == 'SHORT':
                return self.bingx_client.place_market_order(ticker, 'SELL', rounded_quantity)
            else:
                return {
                    'success': False,
                    'error': f"Unknown action: {action}"
                }

        except Exception as e:
            logger.error(f"Trade error: {str(e)}")
            return {
                'success': False,
                'error': f"Trade execution failed: {str(e)}"
            }