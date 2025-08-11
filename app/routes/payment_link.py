# app/routes/payment_link.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal
import time
from ..zoho_client import zoho_request, ACCOUNT_ID

router = APIRouter(prefix="/payments", tags=["payment-link"])

PLAN_MAP = {
    "newbie":   {"amount": 499.0,  "description": "Newbie – 1 Year"},
    "investor": {"amount": 999.0,  "description": "Investor – 1 Year"},
    "trader":   {"amount": 1999.0, "description": "Trader – 1 Year"},
}

class PlanLinkBody(BaseModel):
    plan: Literal["newbie", "investor", "trader"]
    email: EmailStr
    currency: str = "INR"
    return_url: str = "https://your-domain.com/pay/thank-you"

@router.post("/plan-link")
def create_plan_link(body: PlanLinkBody):
    cfg = PLAN_MAP[body.plan]
    payload = {
        "amount": cfg["amount"],
        "currency": body.currency,
        "email": body.email,
        "description": cfg["description"],
        "return_url": body.return_url,
        # use reference_id to tag the plan (instead of meta_data)
        "reference_id": f"{body.plan}-1y-{int(time.time())}"
    }

    resp = zoho_request(
        "POST",
        f"paymentlinks?account_id={ACCOUNT_ID}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)

    pl = data.get("payment_links") or data
    return {
        "plan": body.plan,
        "amount": cfg["amount"],
        "payment_link_id": pl.get("payment_link_id"),
        "status": pl.get("status"),
        "url": pl.get("url"),
    }