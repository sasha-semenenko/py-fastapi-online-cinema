from decimal import Decimal

import pytest

from sqlalchemy import select
from sqlalchemy.orm import joinedload


from src.models.order import OrderModel, OrderItemModel
from src.models.movies import MovieModel
from src.models.accounts import UserModel


@pytest.mark.asyncio
async def test_add_order(client, db_session):
    default = {
        "user_id": 1,
        "status": "pending",
    }

    response = await client.post("order/add/order/", json=default)
    assert response.status_code == 200, f"Expected 200 status code, but got {response.status_code}"

    response_data = response.json()
    assert response_data["message"] == "Order added successfully!"


@pytest.mark.asyncio
async def test_add_movie_to_the_order_item(
        client,
        db_session
):
    request = await db_session.execute(select(UserModel).limit(1))
    user = request.scalars().first()
    assert user is not None, "Expected user is in database!"

    request = await db_session.execute(select(MovieModel).limit(1))
    movie = request.scalars().first()
    assert movie is not None, "Expected movie is in database!"

    response = await client.post(
        "order/add/order/movie/",
        params={"user_id": user.id, "movie_id": movie.id, "price_item_order": 10}
    )
    assert response.status_code == 200, f"Expected 200 status code, but got {response.status_code}"

    data = response.json()

    assert movie.id == data["movie_id"]


@pytest.mark.asyncio
async def test_get_users_orders(client, db_session):

    request = await db_session.execute(select(UserModel).limit(1))
    user = request.scalars().first()
    assert user is not None, "Expected user is in database!"

    request = await db_session.execute(select(OrderModel)
                               .options(joinedload(OrderModel.order_item).joinedload(OrderItemModel.movie))
                               .where(OrderModel.user_id == user.id)
                               )
    order = request.scalars().first()
    assert order is not None, "Expected order is in database!"

    request = await client.get("order/orders/", params={"user_id": user.id})
    assert request.status_code == 200, "Expected orders are exist in database!"

    data = request.json()

    assert order.total_amount == Decimal(data["total_amount"])
    assert order.status == data["status"]
