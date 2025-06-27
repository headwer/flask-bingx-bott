import os
import time
import hmac
import hashlib
import requests
import logging

logger = logging.getLogger(__name__)

class BingXClient:
    BASE_URL = "https://open-api.bingx.com"

    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key or os.getenv("BINGX_API_KEY")
        self.secret_key = api_secret or os.getenv("BINGX_API_SECRET")

        # ⚠️ Quitar esta validación si estás seguro que ya estaban bien cargadas en entorno:
        if not self.api_key or not self.secret_key:
            logger.warning("API keys not found — check env vars.")
            # No detenemos la app, solo avisamos

    def _sign(self, params):
        query = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(self.secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
        return signature

    def get_account_balance(self):
        url = f"{self.BASE_URL}/openApi/swap/v2/user/balance"
        timestamp = str(int(time.time() * 1000))
        params = {"timestamp": timestamp}
        params["signature"] = self._sign(params)
        headers = {"X-BX-APIKEY": self.api_key}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        logger.debug(f"Raw balance response: {data}")
        if data.get("code") == 0:
            return {"success": True, "data": data.get("data")}
        return {"success": False, "error": data.get("msg")}

    def place_market_order(self, symbol, side, quantity):
        url = f"{self.BASE_URL}/openApi/swap/v2/trade/order"
        timestamp = str(int(time.time() * 1000))
        side_value = 1 if side.upper() == "BUY" else 2
        params = {
            "symbol": symbol,
            "side": side_value,
            "price": 0,
            "vol": quantity,
            "leverage": 1,
            "tradeType": 1,
            "action": 1,
            "timestamp": timestamp
        }
        params["signature"] = self._sign(params)
        headers = {"X-BX-APIKEY": self.api_key}
        response = requests.post(url, headers=headers, data=params)
        result = response.json()
        logger.debug(f"Order response: {result}")
        if result.get("code") == 0:
            return {"success": True, "order_id": result.get("data", {}).get("orderId"), "status": "filled"}
        return {"success": False, "error": result.get("msg")}