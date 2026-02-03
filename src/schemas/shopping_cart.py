from datetime import datetime
from typing import List, Text

import uuid
from pydantic import BaseModel
from pydantic.fields import Field

from schemas.examples.shopping_cart import cart_item_list_schema, movie_cart_list_item_schema
from schemas.movies import GenreSchema


class CartItemResponseSchema(BaseModel):
    message: str


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


class CartListResponseSchema(BaseModel):
    cart_id: int
    movies: List[dict]
    added_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [cart_item_list_schema]
        }
    }
