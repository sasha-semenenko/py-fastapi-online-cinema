from __future__ import annotations
from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from src.models.base import Base
from src.models.order import OrderModel

if TYPE_CHECKING:
    from src.models.accounts import UserModel
    from src.models.movies import MovieModel



class CartModel(Base):
    __tablename__ = "cart_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(back_populates="cart")
    cart_item: Mapped[List["CartItemModel"]] = relationship(back_populates="cart", cascade="all, delete-orphan")

    order: Mapped["OrderModel"] = relationship(back_populates="cart")

    __table_args__ = (UniqueConstraint("user_id", name="unique_user_id"), {"extend_existing": True})


class CartItemModel(Base):
    __tablename__ = "cart_item_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart_table.id"))
    cart: Mapped["CartModel"] = relationship(back_populates="cart_item")
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies_table.id"))
    movie: Mapped["MovieModel"] = relationship(back_populates="cart_item")
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    __table_args__ = (UniqueConstraint("cart_id", "movie_id", name="unique_user_movie_ids"), {"extend_existing": True})
