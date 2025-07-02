import base64
import requests
from datetime import datetime
from decouple import config
from requests.auth import HTTPBasicAuth

def get_mpesa_access_token():
    consumer_key = config("MPESA_CONSUMER_KEY")
    consumer_secret = config("MPESA_CONSUMER_SECRET")

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    res = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    return res.json().get("access_token")

def generate_password(timestamp):
    shortcode = config("MPESA_SHORTCODE")
    passkey = config("MPESA_PASSKEY")
    data = f"{shortcode}{passkey}{timestamp}"
    encoded = base64.b64encode(data.encode())
    return encoded.decode()

def lipa_na_mpesa(phone_number, amount):
    access_token = get_mpesa_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(timestamp)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": config("MPESA_SHORTCODE"),
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": config("MPESA_SHORTCODE"),
        "PhoneNumber": phone_number,
        "CallBackURL": config("MPESA_CALLBACK_URL"),
        "AccountReference": "EcommerceShop",
        "TransactionDesc": "Order Payment"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )

    return response.json()
