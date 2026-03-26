from decimal import Decimal

import pytest

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.models.payments import PaymentStatus, PaymentModel, PaymentItemModel
from src.models.accounts import UserModel
from src.models.order import OrderModel, OrderItemModel

@pytest.mark.asyncio
async def test_create_payment(client, db_session):
    request = await db_session.execute(select(UserModel))
    user = request.scalars().first()
    if not user or user.is_active is False:
        assert user is not None, "Expected user is active or exist in database!"

    request = await db_session.execute(select(OrderModel).where(OrderModel.user_id == user.id))
    order = request.scalars().first()
    assert order is not None, "Expected order exist in database!"

    payload = {
        "user_id": user.id,
        "order_id": order.id,
        "status": PaymentStatus.Successful,
        "amount": 111,
    }

    response = await client.post("/payments/create/", json=payload)
    assert response.status_code == 200, "expected payload was created in database!"

    data_response = response.json()

    assert payload["user_id"] == data_response.get("user_id")
    assert payload["order_id"] == data_response.get("order_id")
    assert payload["status"] == data_response.get("status")
    assert Decimal(payload["amount"]) == Decimal(data_response.get("amount"))


@pytest.mark.asyncio
async def test_create_payment_item(client, db_session):
    request = await db_session.execute(select(UserModel))
    user = request.scalars().first()
    if not user or user.is_active is False:
        assert user is not None, "Expected user is active or exist in database!"

    request = await db_session.execute(select(PaymentModel))
    payment = request.scalars().first()
    if not payment:
        assert payment is not None, "Expected payment exist in database!"

    request = await db_session.execute(select(OrderModel).where(OrderModel.user_id == user.id))
    order = request.scalars().first()
    assert order is not None, "Expected order exist in database!"

    request = await db_session.execute(select(OrderItemModel).where(OrderItemModel.order_id == order.id))
    order_item = request.scalars().first()
    assert order_item is not None, "Expected order item exist in database!"

    payload = {
        "payment_id": payment.id,
        "order_item_id": order_item.id,
        "price_at_payment": 123
    }

    response = await client.post("/payments/payment-item/create/", json=payload)
    assert response.status_code == 200, "Expected item created in database!"

    data = response.json()

    assert data["payment_id"] == payload["payment_id"]
    assert data["order_item_id"] == payload["order_item_id"]
    assert Decimal(data["price_at_payment"]) == Decimal(payload["price_at_payment"])


@pytest.mark.asyncio
async def test_users_payments(client, db_session):
    request = await db_session.execute(select(UserModel))
    user = request.scalars().first()
    if not user or user.is_active is False:
        assert user is not None, "Expected user is active or exist in database!"

    request = await db_session.execute(select(PaymentModel).options(
        joinedload(PaymentModel.payment_items)
    ).where(PaymentModel.user_id == user.id))
    payment = request.scalars().first()
    assert payment is not None, "Expected payment exist in database!"

    response = await client.get("/payments/users-payments/", params={"user_id": user.id})
    assert response.status_code == 200, "Expected user's payment exist in database"

    data = response.json()

    assert data["date_and_time"] == payment.created_at.strftime("%d %B %Y")
    assert Decimal(data["amount"]) == Decimal(payment.amount)
    assert data["status"] == payment.status
