import os, requests
from dotenv import load_dotenv
from app.token_manager import get_access_token

load_dotenv()
API_ROOT = os.getenv("API_ROOT")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

def zoho_request(method, path, **kwargs):
    token = get_access_token()  # always fresh
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    headers.update(kwargs.pop("headers", {}) or {})
    url = f"{API_ROOT.rstrip('/')}/{path.lstrip('/')}"
    return requests.request(method, url, headers=headers, timeout=30, **kwargs)
