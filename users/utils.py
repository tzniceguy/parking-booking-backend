import random
import requests
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()


def generate_otp():
    """generate a random 6-digit OTP"""
    return random.randint(100000, 999999)


def send_otp(phone_number, otp):
    """sending an OTP to a phone number through SMS service"""
    sms_username = os.getenv("SMS_USERNAME")
    sms_password = os.getenv("SMS_PASSWORD")

    if not sms_username or not sms_password:
        raise ValueError("SMS credentials not found in environment variables")

    url = "https://messaging-service.co.tz/api/sms/v1/test/text/single"
    payload = {
        "from": "OTP",
        "to": phone_number,
        "message": f"Your OTP is {otp}. It is valid for 15 minutes."
    }

    response = requests.post(
        url,
        json=payload,
        auth=HTTPBasicAuth(sms_username, sms_password)
    )
    response.raise_for_status()
    return response