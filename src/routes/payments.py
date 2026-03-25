import json
import os

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.accounts import UserModel
from src.models.payments import PaymentModel, PaymentItemModel, PaymentStatus
from src.schemas.payments import PaymentResponseSchema, PaymentCreateSchema, PaymentItemResponseSchema, \
    PaymentItemCreateSchema, PaymentUserResponseSchema
from src.models.order import OrderModel, OrderItemModel
from src.database.postgres_session import get_postgres_db


load_dotenv()

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL")
STRIPE_WEBHOOK_SECRET= os.getenv("STRIPE_WEBHOOK_SECRET_KEY")


@router.post("/create/", response_model=PaymentResponseSchema)
async def create_payment(data: PaymentCreateSchema, db: AsyncSession = Depends(get_postgres_db)):
    request = await db.execute(select(UserModel).where(UserModel.id == data.user_id))
    user = request.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    request = await db.execute(select(OrderModel).where(OrderModel.id == data.order_id))
    order = request.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")


    payment = PaymentModel(
        user_id=data.user_id,
        order_id=data.order_id,
        status=data.status,
        amount=data.amount
    )
    db.add(payment)
    await db.commit()

    return PaymentResponseSchema.model_validate(payment)


@router.post("/payment-item/create/", response_model=PaymentItemResponseSchema)
async def create_payment_item(data: PaymentItemCreateSchema, db:AsyncSession = Depends(get_postgres_db)):
    request = await db.execute(select(PaymentModel).where(PaymentModel.id == data.payment_id))
    payment = request.scalars().first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    request = await db.execute(select(OrderItemModel).where(OrderItemModel.id == data.order_item_id))
    order_item = request.scalars().first()

    if not order_item:
        raise HTTPException(status_code=404, detail="Order item was not found")

    payment_item = PaymentItemModel(
        payment_id=data.payment_id,
        order_item_id=data.order_item_id,
        price_at_payment=data.price_at_payment
    )

    db.add(payment_item)

    payment.amount += payment_item.price_at_payment

    await db.commit()
    await db.refresh(payment)

    return PaymentItemResponseSchema.model_validate(payment_item)


@router.get("/users-payments/")
async def get_users_payments(user_id: int, db: AsyncSession = Depends(get_postgres_db)):
    request = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = request.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    request = await db.execute(select(PaymentModel).options(
        joinedload(PaymentModel.payment_items)
    ).where(PaymentModel.user_id == user.id))
    payment = request.scalars().first()

    request = await db.execute(select(PaymentItemModel).where(PaymentItemModel.payment_id == payment.id))
    payment_items = request.scalars().all()

    items = [{"price_at_payment": item.price_at_payment} for item in payment_items]

    result = PaymentUserResponseSchema(
        date_and_time=PaymentResponseSchema.model_validate(payment).created_at.strftime("%d %B %Y"),
        amount=PaymentResponseSchema.model_validate(payment).amount,
        status=PaymentResponseSchema.model_validate(payment).status,
        payment_items=items
    )

    return result


"""Implementation Stripe Payments"""
@router.post("/create_checkout_session/")
async def create_checkout_session(payment_id: int, db:AsyncSession = Depends(get_postgres_db)):
    request = await db.execute(select(PaymentModel).options(joinedload(PaymentModel.orders))
                               .where(PaymentModel.id == payment_id)
                               )
    payment = request.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment was not found")

    try:
        checkout_session = await stripe.checkout.Session.create_async(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "USD",
                    "product_data": {
                        "name": f"Order {payment.order_id}"
                    },
                    "unit_amount": int(payment.amount * 100)
                },
                "quantity": 1,
            }],
            mode="payment",
            metadata={"payment_id": payment.id},
            success_url=f"{BASE_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/payments/cancel",
        )
        payment.external_payment_id = checkout_session.id
        await db.commit()
        await db.refresh(payment)

        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/success")
async def payment_success(session_id: str):
    try:
        session = await stripe.checkout.Session.retrieve_async(session_id)

        if session.payment_status == "successful":
            return {"status": "successful", "customer_email": session.customer_details.email}

        return {"status": "refunded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cancel")
async def payment_cancel():
    return {"message": "Payment cancelled"}


@router.post("/webhook/")
async def stripe_webhook(
        request: Request
):
    payload = await request.body()
    stripe_signature = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload, current payload is {payload}")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature, current signature is {stripe_signature}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get("metadata").get("order_id")

        print(f"Order {order_id} is paid")

    return {"status": "success"}
