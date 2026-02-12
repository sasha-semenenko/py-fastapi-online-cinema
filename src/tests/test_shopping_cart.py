import pytest

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.models.accounts import UserModel
from src.models.movies import MovieModel
from src.models.shopping_cart import CartModel, CartItemModel


@pytest.mark.asyncio
async def test_add_movie_to_shopping_cart(client, db_session):

    user_payload = {
        "email": "test@example.com",
        "password": "Pass123q!"
    }

    response = await client.post("/accounts/register/", json=user_payload)
    assert response.status_code == 201, "Expected status code 201 Created"

    data = response.json()
    assert data["email"] == user_payload["email"], "Expected that emails are equal!"

    request = await db_session.execute(select(UserModel).where(UserModel.email == user_payload["email"]))
    user = request.scalar_one_or_none()
    assert user is not None, "Expected user created is database"

    request = await db_session.execute(select(CartModel).where(CartModel.user_id == user.id))
    cart = request.scalar_one_or_none()
    assert cart is not None, "Expected cart exist in database"

    request = await db_session.execute(select(MovieModel).limit(1))
    movie = request.scalar_one_or_none()
    assert movie is not None, "Expected movie exist in database"

    response = await client.post("/shopping/movie/add/", params={"user_id": user.id, "movie_id": movie.id})
    assert response.status_code == 200, f"Expected status code is 200, actual status code is {response.status_code}"


@pytest.mark.asyncio
async def test_delete_movie_from_car_item(client, db_session):
    request = await db_session.execute(select(CartModel).limit(1))
    cart = request.scalar_one_or_none()
    assert cart is not None, "Expected cart exist in database!"

    request = await db_session.execute(select(MovieModel).limit(1))
    movie = request.scalar_one_or_none()
    assert movie is not None, "Expected movie exist in database!"

    request = await db_session.execute(
        select(CartItemModel)
        .options(joinedload(CartItemModel.movie))
        .where(CartItemModel.cart_id==cart.id)
        .where(CartItemModel.movie_id==movie.id)
        .limit(1)
    )
    cart_item = request.scalar_one_or_none()
    assert cart_item is not None, "Expected cart item exist in database!"

    response = await client.delete("/shopping/movie/delete/", params={"cart_id": cart.id, "movie_id": movie.id})
    assert response.status_code == 200, f"Expected status code 200, actual status code is {response.status_code}"

    request = await db_session.execute(
        select(CartItemModel)
        .options(joinedload(CartItemModel.movie))
        .where(CartItemModel.cart_id==cart.id)
        .where(CartItemModel.movie_id==movie.id)
    )
    cart_item = request.scalar_one_or_none()
    assert cart_item is None, f"Cart item with ID {cart_item.id} was deleted!"


@pytest.mark.asyncio
async def test_get_list_movies_by_user(client, db_session):
    user_payload = {
        "email": "test@example.com",
        "password": "Pass123q!"
    }

    request = await db_session.execute(select(UserModel).where(UserModel.email == user_payload["email"]))
    user = request.scalar_one_or_none()
    assert user is not None, "Expected user exist in database!"

    response = await client.get("/shopping/lists/", params={"user_id": user.id})
    assert response.status_code == 200, f"Expected status code 200, actual status code is {response.status_code}"

    request = await db_session.execute(select(CartModel).where(CartModel.user_id == user.id))
    cart = request.scalar_one_or_none()
    assert cart is not None, "Expected cart exist in database!"

    data = response.json()
    assert cart.id == data["cart_id"], "Expected cart exist in database!"


@pytest.mark.asyncio
async def test_delete_cart_entirely(client, db_session):
    user_payload = {
        "email": "test@example.com",
        "password": "Pass123q!"
    }

    request = await db_session.execute(select(UserModel).where(UserModel.email == user_payload["email"]))
    user = request.scalar_one_or_none()
    assert user is not None, "Expected user exist in database!"

    request = await db_session.execute(select(CartModel).where(CartModel.user_id == user.id))
    cart = request.scalar_one_or_none()
    assert cart is not None, "Expected cart exist in database!"

    cart_id = cart.id
    response = await client.delete(f"/shopping/delete/{cart_id}/")
    assert response.status_code == 200, f"Expected status code is 200, but {response.status_code}"

    request = await db_session.execute(select(CartModel).where(CartModel.id == cart_id))
    cart = request.scalar_one_or_none()
    assert cart is None, "Expected cart does not exist in database!"
