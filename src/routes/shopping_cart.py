import datetime

from fastapi import APIRouter, Depends, HTTPException

from schemas.shopping_cart import CartListResponseSchema, MovieCartListItemSchema
from src.models.movies import MovieModel
from src.models.shopping_cart import CartModel, CartItemModel
from src.schemas.shopping_cart import CartItemResponseSchema
from src.database.postgres_session import get_postgres_db
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


router = APIRouter()


@router.post(
    "/movie/add/",
    summary="Added movie to the cart",
    description="This endpoint allows user added new movie to the cart using user and movie ids.",
    responses={
        200: {
            "description": "Movie was added successfully."
        },
        400: {
            "description": "Invalid input data.",
            "application/json": {
                "example": {
                    "detail": "Invalid input data."
                }
            }
        }
    },
    status_code=200
)
async def add_movie_to_shopping_cart(
        user_id: int,
        movie_id: int,
        db:AsyncSession = Depends(get_postgres_db)
) -> CartItemResponseSchema:
    request = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = request.scalars().first()
    if movie.purchased is True:
        raise HTTPException(status_code=404, detail="You can not pick the same movie twice.")

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    else:
        movie.purchased = True
        await db.commit()

    request = select(CartModel).where(CartModel.user_id == user_id)
    response = await db.execute(request)
    cart = response.scalars().first()
    if not cart:
        cart = CartModel(user_id=user_id)
        db.add(cart)

    cart_item = CartItemModel(cart=cart, movie_id=movie_id)
    db.add(cart_item)
    await db.commit()

    return CartItemResponseSchema(message="Movie was added successfully.")


@router.delete(
    "/movie/delete/",
    summary="Delete movie from the cart",
    description="Deleting with the specific movie from the cart. "
                "If the movie exist it will be deleted, else 404 will be raised.",
    responses={
        204: {"description": "Movie was successfully deleted from the cart."},
        404: {
            "description": "Movie was not found",
            "content": {"application/json": {"example": {"detail": "Movie with the given id was not found."}}}
        }
    })
async def delete_movie_from_shopping_cart(
        cart_id: int,
        movie_id: int,
        db:AsyncSession = Depends(get_postgres_db)
) -> CartItemResponseSchema:

    request = await db.execute(select(CartItemModel).options(joinedload(CartItemModel.movie)).where(CartItemModel.cart_id == cart_id).where(CartItemModel.movie_id == movie_id))
    cart_item = request.scalars().first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart Item not found")

    cart_item.movie.purchased = False

    await db.delete(cart_item)
    await db.commit()

    return CartItemResponseSchema(message="Movie was deleted from cart successfully.")


@router.get(
    "/lists/",
    response_model=CartListResponseSchema,
    summary="Get list of movies in user's shopping cart",
    description="This endpoint allows user's obtain full description of movies in yours shopping cart.",
    responses={
        404: {"description": "Shopping cart was not found.",
              "content": {"application/json": {"example": {"detail": "Shopping cart was not found."}}}
              }
    })
async def get_list_movies_by_user (user_id: int, db: AsyncSession = Depends(get_postgres_db)) -> CartListResponseSchema:

    request = await db.execute(select(CartModel).where(CartModel.user_id == user_id))
    cart = request.scalars().first()
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found.")

    request = await db.execute(select(MovieModel).options(joinedload(MovieModel.genres)))
    movies = request.scalars().unique().all()
    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found")

    request = await db.execute(select(CartItemModel).where(CartItemModel.cart_id == cart.id))
    cart_item = request.scalars().first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Shopping cart item not found.")

    movie = [
        {"id": MovieCartListItemSchema.model_validate(data).id,
         "name": MovieCartListItemSchema.model_validate(data).name,
         "price": MovieCartListItemSchema.model_validate(data).price,
         "year": MovieCartListItemSchema.model_validate(data).year,
         "genres": MovieCartListItemSchema.model_validate(data).genres
         }
        for data in movies if data.purchased
    ]

    response = CartListResponseSchema(
        cart_id=cart.id,
        movies=movie,
        added_at = datetime.datetime.now()
    )

    return response


@router.delete(
    "/delete/{cart_id}/",
    summary="Delete shopping cart entirely",
    description="User can delete shoppingcart entirely despite of many movies there are.",
    responses = {
        204: {"description": "Shopping cart was successfully delete."},
        404: {
            "description": "Shopping cart was not found.",
            "content": {"application/json": {"example": {"detail": "Shopping cart with the given id was not found"}}}
        },
    })
async def delete_shopping_cart_entirely(cart_id: int, db:AsyncSession = Depends(get_postgres_db)) -> CartItemResponseSchema:
    request = await db.execute(select(CartModel).
                               options(joinedload(CartModel.cart_item).joinedload(CartItemModel.movie))
                               .where(CartModel.id == cart_id))
    cart = request.scalars().first()
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found.")

    request = await db.execute(select(CartItemModel).where(CartItemModel.cart_id == cart.id))
    cart_item = request.scalars().all()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Shopping cart item not found.")

    request = await db.execute(select(MovieModel)
                               .join(MovieModel.cart_item)
                               .where(CartItemModel.cart_id == cart_id)
                               )
    movies = request.scalars().unique().all()
    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found.")

    for movie in movies:
        if movie.purchased:
            movie.purchased = False

    await db.delete(cart)
    await db.commit()

    return CartItemResponseSchema(message="Cart delete successfully.")