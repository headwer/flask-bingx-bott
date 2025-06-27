import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles TradingView webhook signals and executes trades"""

    def __init__(self):
        self.bingx_client = BingXClient()

    def execute_trade(self, action: str, ticker: str, quantity: float = None) -> dict:
        try:
            logger.info(f"🚀 Executing trade: {action} {ticker}")

            if action not in ['BUY', 'SELL']:
                return {'success': False, 'error': f"Invalid action: {action}"}

            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {'success': False, 'error': "API keys not configured."}

            if not self.bingx_client.test_connection():
                return {'success': False, 'error': "Failed to connect to BingX API."}

            account_info = self.bingx_client.get_account_balance()
            if not account_info['success']:
                return {'success': False, 'error': f"Failed to fetch balance: {account_info.get('error', '')}"}

            balance_data = account_info['data']
            usdt_info = balance_data.get('balance', {})

            if not usdt_info or 'availableMargin' not in usdt_info:
                return {'success': False, 'error': "USDT balance data missing or invalid from API."}

            balance = float(usdt_info['availableMargin'])
            if balance <= 0:
                return {'success': False, 'error': "No available USDT balance to trade."}

            qty = quantity or (balance / 7)
            logger.info(f"✅ Available USDT: {balance} → Quantity to trade: {qty}")

            # Usar ticker original **con guion medio**
            symbol = ticker.upper()
            logger.debug(f"Using symbol for API: {symbol}")

            symbol_info = self.bingx_client.get_symbol_info(symbol)
            if not symbol_info['success']:
                return {'success': False, 'error': f"Invalid trading pair: {symbol}. {symbol_info.get('error', '')}"}

            rounded_quantity = round(qty, 6)

            result = self.bingx_client.place_market_order(
                symbol=symbol,
                side=action,
                quantity=rounded_quantity
            )

            if result['success']:
                logger.info(f"✅ Trade executed: {result}")
                return {
                    'success': True,
                    'order_id': result.get('order_id'),
                    'symbol': symbol,
                    'side': action,
                    'quantity': rounded_quantity,
                    'status': result.get('status'),
                    'message': f"Executed {action} order for {rounded_quantity} {symbol}"
                }
            else:
                logger.error(f"❌ Trade failed: {result}")
                return {'success': False, 'error': result.get('error', 'Unknown error')}

        except Exception as e:
            logger.error(f"❌ Trade error: {str(e)}")
            return {'success': False, 'error': f"Trade execution failed: {str(e)}"}

    def test_connection(self) -> bool:
        return self.bingx_client.test_connection()

    def get_account_info(self) -> dict:
        return self.bingx_client.get_account_balance()