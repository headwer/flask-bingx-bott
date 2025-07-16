import logging
from bingx_client import BingXClient

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles TradingView webhook signals and executes trades"""

    def __init__(self):
        self.bingx_client = BingXClient()
        self.open_positions = {
            "LONG": [],
            "SHORT": []
        }

    def execute_trade(self, action: str, ticker: str, precio_entrada: float, take_profit: float, stop_loss: float) -> dict:
        """
        Execute a trade with limit entry and bracket TP/SL
        """
        try:
            logger.info(f"Received trade: {action} {ticker} @ {precio_entrada}, TP={take_profit}, SL={stop_loss}")

            # Validar acción
            if action not in ['BUY', 'SELL']:
                return {'success': False, 'error': f"Acción inválida: {action}"}

            position_side = 'LONG' if action == 'BUY' else 'SHORT'

            # Verificar API
            if not self.bingx_client.api_key or not self.bingx_client.secret_key:
                return {'success': False, 'error': "API keys no configuradas"}

            if not self.bingx_client.test_connection():
                return {'success': False, 'error': "Error de conexión con BingX"}

            # Obtener balance
            account_info = self.bingx_client.get_account_balance()
            data = account_info.get('data')
            usdt_balance = next((item for item in data if item.get('asset') == 'USDT'), None)
            balance = float(usdt_balance['available'])
            quantity = round(balance / 4, 6)  # dividir entre 4 partes

            # 🔁 Cerrar posición opuesta si existe
            opuesta = 'SHORT' if position_side == 'LONG' else 'LONG'
            if self.open_positions[opuesta]:
                logger.info(f"Cerrando posición opuesta: {opuesta}")
                for o in self.open_positions[opuesta]:
                    self.bingx_client.close_order(o['order_id'])
                self.open_positions[opuesta] = []

            # 📥 Colocar orden LÍMITE con TP y SL
            logger.info(f"Colocando orden LÍMITE {position_side}: qty={quantity} entry={precio_entrada}, TP={take_profit}, SL={stop_loss}")
            result = self.bingx_client.place_limit_order_with_tp_sl(
                symbol=ticker,
                side=action,
                position_side=position_side,
                quantity=quantity,
                price=precio_entrada,
                take_profit=take_profit,
                stop_loss=stop_loss
            )

            if result['success']:
                order_id = result['order_id']
                self.open_positions[position_side].append({
                    'order_id': order_id,
                    'tp': take_profit
                })

                # 🔁 Si hay más de una entrada en la misma dirección, actualizar el TP global al último
                if len(self.open_positions[position_side]) > 1:
                    latest_tp = take_profit
                    logger.info(f"Actualizando TP global de todas las órdenes {position_side} a {latest_tp}")
                    for o in self.open_positions[position_side]:
                        self.bingx_client.update_take_profit(o['order_id'], latest_tp)

                return {
                    'success': True,
                    'message': f"Orden límite colocada {position_side}",
                    'order_id': order_id,
                    'symbol': ticker,
                    'side': action,
                    'quantity': quantity
                }

            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Error desconocido')
                }

        except Exception as e:
            logger.error(f"Trade error: {str(e)}")
            return {'success': False, 'error': f"Trade execution failed: {str(e)}"}