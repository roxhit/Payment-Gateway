# app/routes/webhooks.py
import os, hmac, hashlib, time, json
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.api_route("/zoho-payments", methods=["GET", "HEAD"])
def webhook_ping():
    return {"ok": True}

SIGNING_KEY = os.getenv("ZOHO_WEBHOOK_SIGNING_KEY", "")
DISABLE_WEBHOOK_SIG = os.getenv("DISABLE_WEBHOOK_SIG", "0") == "1"
MAX_SKEW_SECONDS = 300  # 5 min

print("ZOHO key loaded:", "yes" if SIGNING_KEY else "no")
def valid_signature(sig_header: str, raw_body: bytes) -> bool:
    if DISABLE_WEBHOOK_SIG:       # <-- dev-only bypass
        return True
    if not SIGNING_KEY:
        return False
    # header format: "t=1734340423138,v=<hex>"
    parts = dict(
        x.split("=", 1) for x in (sig_header or "").split(",") if "=" in x
    )
    t = parts.get("t", "")
    v = (parts.get("v") or "").lower()
    if not (t and v):
        return False
    try:
        if abs(time.time() - (int(t) / 1000.0)) > MAX_SKEW_SECONDS:
            return False
    except Exception:
        return False
    message = f"{t}.{raw_body.decode('utf-8')}".encode("utf-8")
    calc = hmac.new(SIGNING_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest().lower()
    return hmac.compare_digest(calc, v)

@router.post("/zoho-payments")
async def zoho_payments_webhook(
    request: Request,
    x_zoho_webhook_signature: str | None = Header(None, convert_underscores=False)
):
    raw = await request.body()
    if not valid_signature(x_zoho_webhook_signature or "", raw):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    # Minimal parse
    event = (payload.get("event") or payload.get("event_type") or "").lower()
    data  = payload.get("data") or payload
    pl    = data.get("payment_link") or data.get("payment_links") or {}
    link_id = pl.get("payment_link_id") or pl.get("id")
    status  = (pl.get("status") or "").lower()

    # TODO: update Mongo here (paid/expired/canceled), kick off invoice
    # (keep this route FAST; do heavy work async if needed)

    return JSONResponse({"ok": True, "event": event, "payment_link_id": link_id, "status": status})
