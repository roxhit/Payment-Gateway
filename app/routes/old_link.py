# app/routes/payment_link.py
from fastapi import APIRouter, HTTPException
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from ..zoho_client import zoho_request, ACCOUNT_ID  # note the two dots (relative import)

router = APIRouter(prefix="/payments", tags=["payment-link"])

class CreatePaymentLinkBody(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    email: EmailStr
    description: str = "Test payment"
    return_url: str = "https://example.com/success"

@router.post("/create-link")
def create_payment_link(body: CreatePaymentLinkBody):
    payload = body.model_dump()
    resp = zoho_request(
        "POST",
        f"paymentlinks?account_id={ACCOUNT_ID}",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)

    # Zoho typically returns { "payment_links": { ... } }
    pl = data.get("payment_links") or data
    return {
        "payment_link_id": pl.get("payment_link_id"),
        "status": pl.get("status"),
        "url": pl.get("url"),
        "raw": data
    }

@router.get("/link/{payment_link_id}")
def get_payment_link(payment_link_id: str):
    resp = zoho_request(
        "GET",
        f"paymentlinks/{payment_link_id}?account_id={ACCOUNT_ID}"
    )
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)
    return data