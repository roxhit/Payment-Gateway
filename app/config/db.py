# config.py
import os
from dotenv import load_dotenv

# Load variables from .env at startup
load_dotenv()

ZOHO_API_ROOT = os.getenv("API_ROOT", "https://payments.zoho.in/api/v1")
ZOHO_ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ZOHO_OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")

print("Zoho API configuration loaded:")
print(f"API_ROOT: {ZOHO_API_ROOT}")
print(f"ACCOUNT_ID: {ZOHO_ACCOUNT_ID}")
print(f"OAUTH_TOKEN: {ZOHO_OAUTH_TOKEN}")

if not ZOHO_ACCOUNT_ID or not ZOHO_OAUTH_TOKEN:
    raise RuntimeError("Zoho credentials are missing in .env file")
