import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles TradingView webhook signals and executes trades"""
    
    def __init__(self):
        self.bingx_client = BingXClient()
    
    def execute_trade(self, action: str, ticker: str, quantity: float) -> dict:
        """
        Execute a trade based on webhook signal
        
        Args:
            action: 'BUY' or 'SELL'
            ticker: Trading pair (e.g., 'BTC-USDT')
            quantity: Trade quantity
        """
        try:
            logger.info(f"Executing trade: {action} {quantity} {ticker}")
            
            # Validate inputs
            if action not in ['BUY', 'SELL']:
                return {
                    'success': False,
                    'error': f"Invalid action: {action}"
                }
            
            if quantity <= 0:
                return {
                    'success': False,
                    'error': f"Invalid quantity: {quantity}"
                }
            
            # Check if BingX client is properly configured
            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {
                    'success': False,
                    'error': "BingX API credentials not configured. Please set BINGX_API_KEY and BINGX_SECRET_KEY environment variables."
                }
            
            # Test connection first
            if not self.bingx_client.test_connection():
                return {
                    'success': False,
                    'error': "Failed to connect to BingX API. Please check your credentials."
                }
            
            # Get symbol info to validate ticker
            symbol_info = self.bingx_client.get_symbol_info(ticker)
            if not symbol_info['success']:
                return {
                    'success': False,
                    'error': f"Invalid trading pair: {ticker}. {symbol_info.get('error', '')}"
                }
            
            # Round quantity to appropriate precision
            # Most crypto pairs support 6-8 decimal places
            rounded_quantity = round(quantity, 6)
            
            # Execute the market order
            result = self.bingx_client.place_market_order(
                symbol=ticker,
                side=action,
                quantity=rounded_quantity
            )
            
            if result['success']:
                logger.info(f"Trade executed successfully: {result}")
                return {
                    'success': True,
                    'order_id': result.get('order_id'),
                    'symbol': ticker,
                    'side': action,
                    'quantity': rounded_quantity,
                    'status': result.get('status'),
                    'message': f"Successfully executed {action} order for {rounded_quantity} {ticker}"
                }
            else:
                logger.error(f"Trade execution failed: {result}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown trading error')
                }
                
        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {
                'success': False,
                'error': f"Trade execution failed: {str(e)}"
            }
    
    def test_connection(self) -> bool:
        """Test connection to BingX API"""
        return self.bingx_client.test_connection()
    
    def get_account_info(self) -> dict:
        """Get account balance information"""
        return self.bingx_client.get_account_balance()
