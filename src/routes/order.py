from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.postgres_session import get_postgres_db
from src.models.movies import MovieModel
from src.schemas.order import OrderAddSchema, OrderCreateSchema, OrderItemSchema, OrderResponseSchema, \
    MovieCartListItemSchema
from sqlalchemy import select

from decimal import Decimal

from src.models.accounts import UserModel
from src.models.order import OrderModel, OrderItemModel
from src.models.shopping_cart import CartModel

router = APIRouter()


@router.post(
    "/add/order/",
    response_model=OrderAddSchema,
    summary="User can place order for movies in their cart",
    description="This endpoint allows user added movie to the order in their cart with the given user's id and movie id",
    responses={
        "200": {"detail": "Order was added successfully!"},
        "400": {"detail": "Invalid input data!", "application/json": {"example": {"detail": "Invalid input data!"}}},
    }
)
async def add_order(data_order: OrderCreateSchema, db: AsyncSession = Depends(get_postgres_db)) -> OrderAddSchema:

    request = await db.execute(select(UserModel).where(UserModel.id == data_order.user_id))
    user = request.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with the id: {data_order.user_id} does not exist!")

    request = await db.execute(select(OrderModel).where(OrderModel.user_id == data_order.user_id))
    order = request.scalars().first()

    request = await db.execute(select(CartModel).where(CartModel.user_id == data_order.user_id))
    cart = request.scalars().first()
    if not cart:
        raise HTTPException(status_code=404, detail=f"Cart with the user id {data_order.user_id} does not exist!")

    if order:
        raise HTTPException(status_code=404, detail=f"You can not add order with id user: {data_order.user_id}")
    else:
        order = OrderModel(user_id=data_order.user_id, status=data_order.status, cart_id=cart.id)
        db.add(order)
        await db.commit()

    return OrderAddSchema(message="Order added successfully!")


@router.post(
    "/add/order/movie/",
    response_model=OrderItemSchema,
    summary="Added movie to the order item",
    description="This endpoints allows user's added movies to the order with the given order id and movie id",
    responses={
        200: {"detail": "Order item was added successfully!"},
        400: {"detail": "invalid input data", "application/json": {"example": {"detail": "Invalid input data!"}}},
    }
)
async def add_movie_to_order_item(
        user_id: int,
        movie_id: int,
        price_item_order: Decimal,
        db: AsyncSession = Depends(get_postgres_db)
) -> OrderItemSchema:

    request = await db.execute(select(OrderModel).where(OrderModel.user_id == user_id))
    order = request.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order was not created! Pleas return and create order first!!!")

    request = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = request.scalars().first()
    if not movie or movie.purchased is True:
        raise HTTPException(status_code=404, detail=f"Movie with the id {movie_id} was not created or is purchased!!!")

    request = await db.execute(select(OrderItemModel)
                               .options(joinedload(OrderItemModel.movie))
                               .where(OrderItemModel.order_id == order.id)
                               .where(OrderItemModel.movie_id == movie_id)
                               )
    order_item = request.scalars().first()
    if order_item:
        raise HTTPException(status_code=404, detail="Order item already exist!")
    else:
        order_item = OrderItemModel(
            order_id=order.id,
            movie_id=movie_id,
            price_at_order=price_item_order,
        )
        db.add(order_item)

    order.total_amount += order_item.price_at_order

    await db.commit()
    await db.refresh(order)

    response = OrderItemSchema(
        order_id=order_item.order_id,
        movie_id=order_item.movie_id,
        price_at_order=order_item.price_at_order
    )

    return response


@router.get(
    "/orders/",
    response_model=OrderResponseSchema,
    summary="Get all user's orders",
    description="This endpoint returns all user's orders by his id's",
    responses={
        200: {"detail": "All orders was return successfully!"},
        204: {"detail": "Orders does not exist", "application/json": {"example": {"detail": "Orders does not exist"}}},
    }
)
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_postgres_db)) -> OrderResponseSchema:

    request = await db.execute(select(OrderModel)
                               .options(joinedload(OrderModel.order_item).joinedload(OrderItemModel.movie))
                               .where(OrderModel.user_id == user_id)
                               )
    order = request.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="User's orders does not exist!")

    request = await db.execute(select(MovieModel).options(joinedload(MovieModel.genres)))
    movies = request.scalars().unique().all()
    if not movies:
        raise HTTPException(status_code=404, detail="Movies does not exist!")

    order_movies = [
        {"id": MovieCartListItemSchema.model_validate(movie).id,
         "name": MovieCartListItemSchema.model_validate(movie).name
         }
        for movie in movies if movie.id == order.order_item.movie_id]


    response = OrderResponseSchema(
        date_time=order.created_at,
        movies=order_movies,
        total_amount=order.total_amount,
        status=order.status
    )

    return response
