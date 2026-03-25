import decimal
import enum
from datetime import datetime

from src.models.order import OrderItemModel
from src.models.accounts import UserModel
from src.models.order import OrderModel
from src.models.base import Base

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, Enum, DECIMAL, String


class PaymentStatus(str, enum.Enum):
    Successful = "successful"
    Canceled = "canceled"
    Refunded = "refunded"


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    users: Mapped["UserModel"] = relationship(back_populates="payments")
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    orders: Mapped["OrderModel"] = relationship(back_populates="payments")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    status: Mapped["PaymentStatus"] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.Successful)
    amount: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    payment_items: Mapped["PaymentItemModel"] = relationship(back_populates="payments")


class PaymentItemModel(Base):
    __tablename__ = "payment_items"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    payments: Mapped["PaymentModel"] = relationship(back_populates="payment_items")
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), nullable=False)
    order_item: Mapped["OrderItemModel"] = relationship(back_populates="payment_items")
    price_at_payment: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)



