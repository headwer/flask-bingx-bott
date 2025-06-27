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
            ticker: Trading pair (e.g., 'BTC-USDT')
            quantity: Optional - calculated automatically from account balance
        """
        try:
            logger.info(f"Executing trade: {action} {ticker}")

            if action not in ['BUY', 'SELL']:
                return {
                    'success': False,
                    'error': f"Invalid action: {action}"
                }

            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {
                    'success': False,
                    'error': "API keys not configured. Set BINGX_API_KEY and BINGX_SECRET_KEY."
                }

            if not self.bingx_client.test_connection():
                return {
                    'success': False,
                    'error': "Failed to connect to BingX API."
                }

            account_info = self.bingx_client.get_account_balance()
            if not account_info['success']:
                return {
                    'success': False,
                    'error': f"Failed to fetch balance: {account_info.get('error', '')}"
                }

            # Validación del formato del balance
            balances = account_info['data']
            if not isinstance(balances, list):
                return {
                    'success': False,
                    'error': "Invalid response format: expected a list of balances"
                }

            usdt_balance = next((item for item in balances if item.get('asset') == 'USDT'), None)
            if not usdt_balance or float(usdt_balance['availableMargin']) <= 0:
                return {
                    'success': False,
                    'error': "No USDT balance available to trade."
                }

            balance = float(usdt_balance['availableMargin'])
            quantity = balance / 7
            logger.info(f"Available USDT balance: {balance} -> Trading quantity: {quantity}")

            # DEBUG EXTRA: imprimir los primeros 10 símbolos válidos para ayudarte a encontrar el correcto
            all_contracts = self.bingx_client.get_symbol_info(symbol=None, list_all=True)
            if isinstance(all_contracts, list):
                logger.debug("⚠️ Lista de contratos disponibles:")
                for contract in all_contracts[:10]:
                    logger.debug(f"➡️  {contract.get('symbol')}")

            # Normaliza símbolo de entrada para la validación
            symbol = ticker.replace('-', '_').upper()
            symbol_info = self.bingx_client.get_symbol_info(symbol)
            if not symbol_info['success']:
                return {
                    'success': False,
                    'error': f"Invalid trading pair: {symbol}. {symbol_info.get('error', '')}"
                }

            rounded_quantity = round(quantity, 6)

            result = self.bingx_client.place_market_order(
                symbol=symbol,
                side=action,
                quantity=rounded_quantity
            )

            if result['success']:
                logger.info(f"Trade executed: {result}")
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
        """Test connection to BingX API"""
        return self.bingx_client.test_connection()

    def get_account_info(self) -> dict:
        """Get account balance"""
        return self.bingx_client.get_account_balance()