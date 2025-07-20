import random
import requests
import os
from dotenv import load_dotenv
import re
load_dotenv()


def generate_otp():
    """generate a random 6-digit OTP"""
    return random.randint(100000, 999999)

def validate_phone_number(phone_number: str) -> str:
    """
    Validate and format Tanzanian phone number to international format without '+'.
    Accepts formats like: '0712345678', '+255712345678', '255712345678'
    Returns: '255712345678'
    """
    phone_number = phone_number.strip().replace(" ", "")

    # Handle local format like 0712345678
    if phone_number.startswith("0") and len(phone_number) == 10:
        phone_number = "255" + phone_number[1:]

    # Remove '+' if present
    phone_number = phone_number.lstrip("+")

    if not re.fullmatch(r"\d{10,14}", phone_number):
        raise ValueError("Invalid phone number format")

    return phone_number


def send_otp(phone_number, otp):
    """sending an OTP to a phone number through SMS service"""
    sms_token = os.getenv("SMS_APIKEY")

    if not sms_token:
        raise ValueError("SMS credentials not found in environment variables")

    #validate and format the phone number
    validated_number = validate_phone_number(phone_number)

    url = "https://api.notify.africa/v2/send-sms"
    payload = {
        "sender_id": "55",
        "schedule":"none",
        "recipients":  [{"number": validated_number}],
        "sms": f"Your egesha OTP is {otp}. It is valid for 15 minutes."
    }
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {sms_token}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        status = getattr(e.response, "status_code", "N/A")
        text = getattr(e.response, "text", "No response body")
        raise Exception(f"Error sending OTP: {e}, Status: {status}, Response: {text}")
