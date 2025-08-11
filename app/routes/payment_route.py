from fastapi import APIRouter, HTTPException
from app.models.payment_model import PaymentModel
from app.config.db import ZOHO_API_ROOT, ZOHO_ACCOUNT_ID, ZOHO_OAUTH_TOKEN
import httpx

payment_router = APIRouter()

headers = {
    "Authorization": f"Zoho-oauthtoken {ZOHO_OAUTH_TOKEN}",
    "Content-Type": "application/json",
}


@payment_router.post("/create-payment-session")
async def create_payment_session(req: PaymentModel):
    if not ZOHO_ACCOUNT_ID or not ZOHO_OAUTH_TOKEN:
        raise HTTPException(status_code=500, detail="Zoho credentials not configured")

    headers = {
        "Authorization": f"Zoho-oauthtoken {ZOHO_OAUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    # Zoho requires: amount, currency, description
    payload = {
        "amount": int(req.amount * 100),  # convert to paise
        "currency": "INR",
        "customer": {"name": req.customer_name, "email": req.customer_email},
        "description": f"Payment for {req.plan_name}",
    }

    url = f"{ZOHO_API_ROOT}/paymentsessions?account_id={ZOHO_ACCOUNT_ID}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        return resp.json()


@payment_router.get("/payment/{payment_id}")
async def get_payment(payment_id: str):
    url = f"{ZOHO_API_ROOT}/payments/{payment_id}?account_id={ZOHO_ACCOUNT_ID}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
