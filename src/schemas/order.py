import uuid

from decimal import Decimal
from datetime import datetime
from typing import List, Text

from pydantic.fields import Field
from pydantic.main import BaseModel

from schemas.examples.shopping_cart import movie_cart_list_item_schema
from schemas.movies import GenreSchema
from src.models.order import OrderEnumStatus
from src.schemas.examples.order import order_create_schema


class OrderCreateSchema(BaseModel):
    user_id: int
    status: OrderEnumStatus

    model_config = {
        "from_attribute": True,
        "json_schema_extra": order_create_schema
    }


class OrderAddSchema(BaseModel):
    message: str

    model_config = {"from_attribute": True}


class OrderItemSchema(BaseModel):
    order_id: int
    movie_id: int
    price_at_order: Decimal

    model_config = {"from_attribute": True}


class MovieCartListItemSchema(BaseModel):
    id: int
    uuid: uuid.UUID
    name: str = Field(..., max_length=255)
    year: int
    time: int
    imdb: float = Field(..., ge=0)
    votes: int
    meta_score: float = Field(..., ge=0)
    gross: float = Field(..., ge=0)
    description: Text
    price: float = Field(..., ge=0)
    genres: List[GenreSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_cart_list_item_schema
            ]
        }
    }


class OrderResponseSchema(BaseModel):
    date_time: datetime
    movies: List[dict]
    total_amount: Decimal
    status: OrderEnumStatus

    model_config = {"from_attribute": True}
