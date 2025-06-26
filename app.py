import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from webhook_handler import WebhookHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize webhook handler
webhook_handler = WebhookHandler()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/test')
def test_webhook():
    """Test webhook interface"""
    return render_template('test_webhook.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """TradingView webhook endpoint"""
    try:
        # Log incoming request
        logger.info(f"Webhook received: {request.json}")
        
        # Validate content type
        if not request.is_json:
            logger.error("Invalid content type - JSON required")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.json
        
        # Validate required fields (ya no exigimos balance)
        required_fields = ['accion', 'ticker']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        # Validate action
        action = data['accion'].upper()
        if action not in ['BUY', 'SELL']:
            error_msg = f"Invalid action: {action}. Must be 'BUY' or 'SELL'"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        # Ejecutar operación (el balance se obtiene desde BingX dentro del handler)
        result = webhook_handler.execute_trade(
            action=action,
            ticker=data['ticker']
        )
        
        if result['success']:
            logger.info(f"Trade executed successfully: {result}")
            return jsonify({
                'success': True,
                'message': 'Trade executed successfully',
                'order_id': result.get('order_id'),
                'action': action,
                'ticker': data['ticker'],
                'quantity': result.get('quantity')
            }), 200
        else:
            logger.error(f"Trade execution failed: {result}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/test-webhook', methods=['POST'])
def test_webhook_endpoint():
    """Test webhook with form data"""
    try:
        action = request.form.get('action')
        ticker = request.form.get('ticker')
        balance_input = request.form.get('balance')

        if not balance_input:
            flash("❌ Balance field is required.", 'error')
            return redirect(url_for('test_webhook'))

        balance = float(balance_input)
        quantity = balance / 7

        # Execute trade
        result = webhook_handler.execute_trade(
            action=action.upper(),
            ticker=ticker,
            quantity=quantity
        )

        if isinstance(result, dict) and result.get('success'):
            flash(f"✅ Trade executed successfully! Order ID: {result.get('order_id')}", 'success')
        elif isinstance(result, dict):
            flash(f"❌ Trade failed: {result.get('error', 'Unknown error')}", 'error')
        else:
            flash(f"❌ Unexpected response: {str(result)}", 'error')

    except Exception as e:
        flash(f"❌ Error: {str(e)}", 'error')

    return redirect(url_for('test_webhook'))

@app.route('/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'online',
        'webhook_url': '/webhook',
        'bingx_connected': webhook_handler.test_connection()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
