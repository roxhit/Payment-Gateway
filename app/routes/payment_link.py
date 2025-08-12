# app/routes/payment_link.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal
import time

from ..zoho_client import zoho_request, ACCOUNT_ID
from app.config.mongodb import db_catax

router = APIRouter(prefix="/payments", tags=["payment-link"])

PLAN_MAP = {
    "newbie":   {"amount": 1.0,   "description": "Newbie – 1 Year"},
    "investor": {"amount": 999.0, "description": "Investor – 1 Year"},
    "trader":   {"amount": 1999.0,"description": "Trader – 1 Year"},
}

class PlanLinkBody(BaseModel):
    plan: Literal["newbie", "investor", "trader"]
    email: EmailStr
    currency: str = "INR"
    # for dev, override this with your public https page (frontend ngrok)
    return_url: str = "http://localhost:3000/pricing/dummy"

@router.post("/plan-link")
def create_plan_link(body: PlanLinkBody):
    cfg = PLAN_MAP[body.plan]
    create_payload = {
        "amount": cfg["amount"],
        "currency": body.currency,
        "email": body.email,
        "description": cfg["description"],
        "return_url": body.return_url,  # don't modify; Zoho will append params
        "reference_id": f"{body.plan}-1y-{int(time.time())}",
    }

    resp = zoho_request(
        "POST",
        f"paymentlinks?account_id={ACCOUNT_ID}",
        json=create_payload,
        headers={"Content-Type": "application/json"},
    )
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)

    pl = data.get("payment_links") or data
    pl_id = pl.get("payment_link_id")
    if not pl_id:
        raise HTTPException(500, detail={"message": "No payment_link_id in response", "raw": data})

    # Save minimal record in Mongo (source of truth is Zoho / webhooks)
    result_data = {
        "plan": body.plan,
        "amount": cfg["amount"],
        "currency": body.currency,
        "email": body.email,
        "payment_link_id": pl_id,
        "status": pl.get("status"),
        "url": pl.get("url"),
        "created_at": time.time(),
    }

    try:
        insert_result = db_catax.payment_links.insert_one(result_data)
        result_data["_id"] = str(insert_result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error saving to DB", "error": str(e)})

    return result_data

class VerifyBody(BaseModel):
    payment_link_id: str

@router.post("/verify")
def verify_payment_link(body: VerifyBody):
    # Optional: check we created this link
    if not db_catax.payment_links.find_one({"payment_link_id": body.payment_link_id}):
        raise HTTPException(status_code=404, detail={"error": "Payment link ID not found"})

    resp = zoho_request("GET", f"paymentlinks/{body.payment_link_id}?account_id={ACCOUNT_ID}")
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)

    pl = data.get("payment_links") or data
    status = (pl.get("status") or "").lower()  # active | paid | canceled | expired
    return {
        "payment_link_id": body.payment_link_id,
        "status": status,
        "paid": status == "paid",
        "amount": pl.get("amount"),
        "currency": pl.get("currency"),
        "email": pl.get("email"),
        "reference_id": pl.get("reference_id"),
    }
