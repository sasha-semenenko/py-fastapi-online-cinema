from datetime import datetime
from typing import List

from pydantic import BaseModel

from decimal import Decimal

from src.models.payments import PaymentStatus


class PaymentCreateSchema(BaseModel):
    user_id: int
    order_id: int
    status: PaymentStatus
    amount: Decimal

    model_config = {"from_attributes": True}


class PaymentResponseSchema(PaymentCreateSchema):
    id: int
    created_at: datetime


class PaymentItemCreateSchema(BaseModel):
    payment_id: int
    order_item_id: int
    price_at_payment: Decimal

    model_config = {"from_attributes": True}


class PaymentItemResponseSchema(PaymentItemCreateSchema):
    id: int


class PaymentUserResponseSchema(BaseModel):
    date_and_time: str
    amount: Decimal
    status: PaymentStatus
    payment_items: List[dict]
