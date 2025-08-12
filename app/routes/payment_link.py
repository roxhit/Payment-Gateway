# app/routes/payment_link.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import time
from ..zoho_client import zoho_request, ACCOUNT_ID
from app.config.mongodb import db_catax
from bson import ObjectId

router = APIRouter(prefix="/payments", tags=["payment-link"])

PLAN_MAP = {
    "newbie": {"amount": 499.0, "description": "Newbie – 1 Year"},
    "investor": {"amount": 999.0, "description": "Investor – 1 Year"},
    "trader": {"amount": 1999.0, "description": "Trader – 1 Year"},
}


def with_query_param(url: str, key: str, value: str) -> str:
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q[key] = value
    new_query = urlencode(q)
    return urlunparse(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            parts.params,
            new_query,
            parts.fragment,
        )
    )


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
        "reference_id": f"{body.plan}-1y-{int(time.time())}",
    }

    # Create payment link in Zoho
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
        raise HTTPException(
            500, detail={"message": "No payment_link_id in response", "raw": data}
        )

    # Update return_url with payment_link_id
    new_return_url = with_query_param(body.return_url, "payment_link_id", pl_id)
    upd = zoho_request(
        "PUT",
        f"paymentlinks/{pl_id}?account_id={ACCOUNT_ID}",
        json={"return_url": new_return_url},
        headers={"Content-Type": "application/json"},
    )

    # Prepare data for MongoDB
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
    if upd.status_code >= 300:
        result_data["warning"] = {"message": "return_url not updated"}

    # Insert into MongoDB
    try:
        insert_result = db_catax.payment_links.insert_one(result_data)
        result_data["_id"] = str(
            insert_result.inserted_id
        )  # Convert ObjectId to string
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"message": "Error saving to DB", "error": str(e)}
        )

    return result_data


class VerifyBody(BaseModel):
    payment_link_id: str


@router.post("/verify")
def verify_payment_link(body: VerifyBody):
    payment_record = db_catax.payment_links.find_one(
        {"payment_link_id": body.payment_link_id}
    )
    if not payment_record:
        raise HTTPException(
            status_code=404, detail={"error": "Payment link ID not found"}
        )
    resp = zoho_request(
        "GET", f"paymentlinks/{body.payment_link_id}?account_id={ACCOUNT_ID}"
    )
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
    resp = zoho_request(
        "GET", f"paymentlinks/{payment_link_id}?account_id={ACCOUNT_ID}"
    )
    data = resp.json()
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=data)
    pl = data.get("payment_links") or data
    status = (pl.get("status") or "").lower()
    return {
        "payment_link_id": payment_link_id,
        "status": status,
        "paid": status == "paid",
    }
