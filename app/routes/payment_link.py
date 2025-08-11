# app/routes/payment_link.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import time
from ..zoho_client import zoho_request, ACCOUNT_ID

router = APIRouter(prefix="/payments", tags=["payment-link"])

PLAN_MAP = {
    "newbie":   {"amount": 499.0,  "description": "Newbie – 1 Year"},
    "investor": {"amount": 999.0,  "description": "Investor – 1 Year"},
    "trader":   {"amount": 1999.0, "description": "Trader – 1 Year"},
}

def with_query_param(url: str, key: str, value: str) -> str:
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q[key] = value
    new_query = urlencode(q)
    return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))

class PlanLinkBody(BaseModel):
    plan: Literal["newbie", "investor", "trader"]
    email: EmailStr
    currency: str = "INR"
    return_url: str = "https://your-domain.com/pay/thank-you"

@router.post("/plan-link")
def create_plan_link(body: PlanLinkBody):
    cfg = PLAN_MAP[body.plan]
    create_payload = {
        "amount": cfg["amount"],
        "currency": body.currency,
        "email": body.email,
        "description": cfg["description"],
        "return_url": body.return_url,
        "reference_id": f"{body.plan}-1y-{int(time.time())}"
    }
    resp = zoho_request(
        "POST",
        f"paymentlinks?account_id={ACCOUNT_ID}",
        json=create_payload,
        headers={"Content-Type": "application/json"}
    )
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)

    pl = data.get("payment_links") or data
    pl_id = pl.get("payment_link_id")
    if not pl_id:
        raise HTTPException(500, detail={"message": "No payment_link_id in response", "raw": data})

    new_return_url = with_query_param(body.return_url, "payment_link_id", pl_id)
    upd = zoho_request(
        "PUT",
        f"paymentlinks/{pl_id}?account_id={ACCOUNT_ID}",
        json={"return_url": new_return_url},
        headers={"Content-Type": "application/json"}
    )
    # don’t fail if update warns — still return usable link
    if upd.status_code >= 300:
        return {
            "plan": body.plan,
            "amount": cfg["amount"],
            "payment_link_id": pl_id,
            "status": pl.get("status"),
            "url": pl.get("url"),
            "warning": {"message": "return_url not updated"}
        }

    return {
        "plan": body.plan,
        "amount": cfg["amount"],
        "payment_link_id": pl_id,
        "status": pl.get("status"),
        "url": pl.get("url"),
        # (optional to keep) "return_url": new_return_url
    }

class VerifyBody(BaseModel):
    payment_link_id: str

@router.post("/verify")
def verify_payment_link(body: VerifyBody):
    resp = zoho_request("GET", f"paymentlinks/{body.payment_link_id}?account_id={ACCOUNT_ID}")
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)

    pl = data.get("payment_links") or data
    status = (pl.get("status") or "").lower()
    return {
        "payment_link_id": body.payment_link_id,
        "status": status,
        "paid": status == "paid",
        "amount": pl.get("amount"),
        "currency": pl.get("currency"),
        "email": pl.get("email"),
        "reference_id": pl.get("reference_id"),
        # drop "raw" in prod to keep responses small
    }

@router.get("/verify-simple")
def verify_simple(payment_link_id: str):
    resp = zoho_request("GET", f"paymentlinks/{payment_link_id}?account_id={ACCOUNT_ID}")
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)
    pl = data.get("payment_links") or data
    status = (pl.get("status") or "").lower()
    return {"payment_link_id": payment_link_id, "status": status, "paid": status == "paid"}
