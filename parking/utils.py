import math
from azampay import Azampay
from dotenv import load_dotenv
import os

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
    """a class to handle payment services"""
    def __init__(self):
        self.app_name = settings.AZAMPAY_CONFIG["APP_NAME"]
        self.client_id = settings.AZAMPAY_CONFIG["CLIENT_ID"]
        self.client_secret = settings.AZAMPAY_CONFIG["CLIENT_SECRET"]
        self.provider = settings.AZAMPAY_CONFIG["PROVIDER"]
        self.environment = settings.AZAMPAY_CONFIG["ENVIRONMENT"]

    def initiate_payment(self, phone_number, amount, booking):
        """utility function to initiate payment for a booking with azampay"""
        checkout = Azampay.mobile_checkout(
            amount=amount,
            mobile=phone_number,
            external_id=booking,
            provider=self.provider)

        # Check if checkout is a dictionary and has 'success' key that is True
        if isinstance(checkout, dict) and checkout.get("success"):
            return {
                "success": True,
                "transaction_id": checkout.get("transaction_id"),
                "message": checkout.get("message", "Payment initiated successfully")
            }
        else:
            # Handle the case where checkout is not a dictionary or doesn't indicate success
            if isinstance(checkout, dict):
                message = checkout.get("message", "Payment initiation failed")
            else:
                # If it's not a dictionary, convert to string for the message
                message = str(checkout) if checkout is not None else "Payment initiation failed with no response"
            return {
                "success": False,
                "message": message
            }
