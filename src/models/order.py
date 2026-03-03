from typing import TYPE_CHECKING

from src.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, Enum, DECIMAL
from datetime import datetime

import enum
import decimal

if TYPE_CHECKING:
    from src.models.accounts import UserModel
    from src.models.movies import MovieModel
    from src.models.shopping_cart import CartModel


class OrderEnumStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderModel(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    status: Mapped[OrderEnumStatus] = mapped_column(Enum(OrderEnumStatus), nullable=False, unique=True)
    total_amount: Mapped[decimal] = mapped_column(DECIMAL(10,2), default=0)

    order_item: Mapped["OrderItemModel"] = relationship(back_populates="order")
    user: Mapped["UserModel"] = relationship(back_populates="orders")

    cart: Mapped["CartModel"] = relationship(back_populates="order")
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart_table.id"))


class OrderItemModel(Base):
    __tablename__ = "order_items"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies_table.id"))
    price_at_order: Mapped[decimal] = mapped_column(DECIMAL(10,2))

    order: Mapped["OrderModel"] = relationship(back_populates="order_item")
    movie: Mapped["MovieModel"] = relationship(back_populates="order_item")
