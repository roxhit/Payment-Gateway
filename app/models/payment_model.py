from pydantic import BaseModel
from typing import Optional


class PaymentModel(BaseModel):
    plan_name: str
    amount: float
    customer_name: str
    customer_email: str
