import os, requests
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from app.token_manager import save_refresh_token

load_dotenv()
router = APIRouter()

ACCOUNTS = os.getenv("ZOHO_ACCOUNTS", "https://accounts.zoho.in")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE", "ZohoPay.payments.CREATE")

AUTH_URL  = f"{ACCOUNTS}/oauth/v2/auth"
TOKEN_URL = f"{ACCOUNTS}/oauth/v2/token"

@router.get("/oauth/start")
def oauth_start():
    params = {
        "scope": SCOPE,
        "client_id": CLIENT_ID,
        "response_type": "code",
        "access_type": "offline",   # gives refresh_token
        "redirect_uri": REDIRECT_URI,
        "prompt": "consent",
    }
    return RedirectResponse(f"{AUTH_URL}?{urlencode(params)}")

@router.get("/callback")
def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing ?code")
    r = requests.post(TOKEN_URL, data={
        "grant_type":"authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }, timeout=30)
    data = r.json()
    if "access_token" not in data:
        raise HTTPException(500, detail=data)

    rt = data.get("refresh_token")
    if rt:  # save one-time
        save_refresh_token(rt)

    def mask(s): 
        return s[:8]+"..."+s[-6:] if s and len(s)>20 else str(s)
    html = f"""
    <html><body style="font-family:system-ui">
      <h2>Zoho linked ✅</h2>
      <p>Access token received (cached automatically).</p>
      <p>Refresh token saved: <code>{mask(rt) if rt else "(unchanged)"}</code></p>
      <p>You can close this tab. Tokens will auto-refresh from now on.</p>
    </body></html>
    """
    return HTMLResponse(html)
