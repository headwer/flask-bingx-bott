import logging
from bingx_client import BingXClient
import uuid

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self):
        self.bingx_client = BingXClient()

    def execute_trade(self, direction: str, ticker: str, entry_price: float,
                      tp_price: float, sl_price: float) -> dict:
        try:
            if direction not in ['BUY', 'SELL']:
                return {'success': False, 'error': f"Invalid direction: {direction}"}

            if not self.bingx_client.test_connection():
                return {'success': False, 'error': "API connection failed."}

            account_info = self.bingx_client.get_account_balance()
            data = account_info.get('data', [])

            if not data or float(data[0].get('available', 0)) <= 0:
                return {'success': False, 'error': "No available balance."}

            total_balance = float(data[0]['available'])
            quantity = total_balance / 4
            quantity = round(quantity, 6)

            group_id = str(uuid.uuid4())  # unique identifier to group related positions

            result = self.bingx_client.place_limit_order(
                symbol=ticker,
                side=direction,
                quantity=quantity,
                entry_price=entry_price,
                tp_price=tp_price,
                sl_price=sl_price,
                group_id=group_id
            )

            if result['success']:
                return {
                    'success': True,
                    'message': f"Limit {direction} order placed.",
                    'order_id': result['order_id'],
                    'group_id': group_id
                }
            return result
        except Exception as e:
            logger.error(f"Webhook execution error: {str(e)}")
            return {'success': False, 'error': str(e)}