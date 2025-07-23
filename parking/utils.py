import math
import uuid
from azampay import Azampay

from config import settings


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance in kilometers between two points on Earth
    using the Haversine formula.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        float: The distance between the two points in kilometers.
    """
    earth_radius = 6371  # Earth radius in kilometers

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius * c

class PaymentService:
    def __init__(self):
        self.app_name = settings.AZAMPAY_CONFIG["APP_NAME"]
        self.client_id = settings.AZAMPAY_CONFIG["CLIENT_ID"]
        self.client_secret = settings.AZAMPAY_CONFIG["CLIENT_SECRET"]
        self.provider = settings.AZAMPAY_CONFIG["PROVIDER"]

        # Initialize Azampay client
        self.client = Azampay(
            app_name=self.app_name,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    def initiate_payment(self, phone_number, amount, booking):
        try:
            checkout = self.client.mobile_checkout(
                amount=amount,
                mobile=phone_number,
                external_id=str(booking),  # Ensure string conversion
                provider=self.provider
            )

            if isinstance(checkout, dict) and checkout.get("success"):
                transaction_id = checkout.get("transactionId")
                if not transaction_id:
                    # Fallback to a unique ID if not provided by the payment gateway
                    transaction_id = f"FALLBACK_{uuid.uuid4()}"
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "external_id": checkout.get("externalId"),
                    "message": checkout.get("message", "Payment initiated")
                }
            else:
                message = checkout.get("message", "Payment failed") if isinstance(checkout, dict) else str(checkout)
                return {"success": False, "message": message}

        except Exception as e:
            # Consider logging the full exception here
            return {"success": False, "message": f"Payment error: {str(e)}"}
