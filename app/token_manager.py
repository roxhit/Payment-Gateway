import os, json, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCOUNTS = os.getenv("ZOHO_ACCOUNTS", "https://accounts.zoho.in")
TOKEN_URL = f"{ACCOUNTS}/oauth/v2/token"

TOKEN_FILE = Path("token_cache.json")    # stores access token + expiry
SECRETS_FILE = Path("zoho_secrets.json") # stores refresh_token

def _read(p: Path):
    if p.exists():
        try: return json.loads(p.read_text())
        except: return {}
    return {}

def _write(p: Path, data: dict):
    p.write_text(json.dumps(data))

def save_refresh_token(rt: str):
    data = _read(SECRETS_FILE)
    data["refresh_token"] = rt
    _write(SECRETS_FILE, data)

def _get_rt():
    rt = _read(SECRETS_FILE).get("refresh_token")
    if not rt:
        raise RuntimeError("No refresh_token yet. Visit /oauth/start once.")
    return rt

def _refresh():
    r = requests.post(TOKEN_URL, data={
        "grant_type":"refresh_token",
        "client_id":CLIENT_ID,
        "client_secret":CLIENT_SECRET,
        "refresh_token":_get_rt(),
    }, timeout=30)
    js = r.json()
    if "access_token" not in js:
        raise RuntimeError(f"Refresh failed: {js}")
    expires_at = int(time.time()) + int(js.get("expires_in",3600)) - 60
    cache = {"access_token": js["access_token"], "expires_at": expires_at}
    _write(TOKEN_FILE, cache)
    return cache

def get_access_token():
    cache = _read(TOKEN_FILE)
    if not cache or int(time.time()) >= cache.get("expires_at",0):
        cache = _refresh()
    return cache["access_token"]
