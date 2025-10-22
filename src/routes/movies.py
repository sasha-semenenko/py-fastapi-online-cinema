from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2 import IntegrityError

from database.postgres_session import get_postgres_db
from models.movies import MovieModel, CertificationModel, GenreModel, StarModel, DirectorModel
from schemas.movies import MovieDetailResponseSchema, MovieCreateSchema, MovieListResponseSchema, MovieListItemSchema, \
    MovieUpdateResponseSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from sqlalchemy import select, func


router = APIRouter()


@router.post(
    "/movie/create/",
    response_model=MovieDetailResponseSchema,
    description="This endpoint allows a new client to add new movie to the database. "
                "It accept details such as name, year, time, genres, stars, directors and other attributes."
                "The associated genres, stars, directors will be created or linked automatically.",
    responses={
        201: {
            "description": "Movie will created successfully"
        },
        400: {
            "description": "invalid input",
            "application/json": {
                "example": {"detail": "Invalid input data"}
            }
        }
    },
    status_code=201
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_postgres_db)
) -> MovieDetailResponseSchema:

    """Add new movie to the database"""

    request = select(MovieModel).where(MovieModel.name == movie_data.name)
    response = await db.execute(request)
    movie = response.scalar_one_or_none()
    if movie:
        raise HTTPException(
            status_code=409,
            detail=f"Movie with such name: {movie_data.name} already exists"
        )

    try:
        #certification
        request = select(CertificationModel).where(CertificationModel.name == movie_data.certification)
        response = await db.execute(request)
        certification = response.scalars().first()
        if not certification:
            certification = CertificationModel(name=movie_data.certification)
            db.add(certification)
            await db.flush()

        # genres
        genres = []
        for genre in movie_data.genres:
            request = select(GenreModel).where(GenreModel.name == genre)
            response = await db.execute(request)
            res = response.scalar_one_or_none()
            if not res:
                genre = GenreModel(name=genre)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        # stars
        stars = []
        for star in movie_data.stars:
            request = select(StarModel).where(StarModel.name == star)
            response = await db.execute(request)
            res = response.scalar_one_or_none()
            if not res:
                star = StarModel(name=star)
                db.add(star)
                await db.flush()
            stars.append(star)

        # directors
        directors = []
        for director in movie_data.directors:
            request = select(DirectorModel).where(DirectorModel.name == director)
            response = await db.execute(request)
            res = response.scalar_one_or_none()
            if not res:
                director = DirectorModel(name=director)
                db.add(director)
                await db.flush()
            directors.append(director)

        movie = MovieModel(
            uuid=movie_data.uuid,
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            gross=movie_data.gross,
            description=movie_data.description,
            price=movie_data.price,
            certification=certification,
            genres=genres,
            stars=stars,
            directors=directors
        )
        db.add(movie)
        await db.commit()
        await db.refresh(movie, ["genres", "stars", "directors"])
        return MovieDetailResponseSchema.model_validate(movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data")


@router.get(
    "movies-list",
    response_model=MovieListResponseSchema,
    summary="Get a paginated list of movies",
    description="This endpoints retrieves pagination movie list from the database."
                "Clients can specified the 'page' number and the number of items per page using 'per_page'."
                "The response includes the details about movies, total pages and total items, "
                "along with links to the previous and next pages if applicable",
    responses={
        404: {
            "description": "Movie not found",
            "content": {
                "application/json": {
                    "example": {"No movies found."}
                }
            }
        }
    }
)
async def get_movies_list(
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        db: AsyncSession = Depends(get_postgres_db)
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page

    request = select(func.count(MovieModel.id))
    response = await db.execute(request)
    total_movies = response.scalar() or 0

    if not total_movies:
        raise HTTPException(status_code=404, detail="Movie not found")

    order_by = MovieModel.default_order_by()

    request = select(MovieModel)
    if order_by:
        request = request.order_by(*order_by)

    request = request.offset(offset).limit(per_page)

    request_movie = await db.execute(request)
    movies = request_movie.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    total_pages = (total_movies + per_page - 1) // per_page

    response = MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"/movies/movies-list/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/movies/movies-list/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_movies,
    )
    return response


@router.get(
    "movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    summary="Get a movie by id",
    description="Fetch detail information about a specific movie by its unique ID."
                "This endpoint retrieves all available details for the movie, such as "
                "uuid, year, name, time, votes. If the movie with the given ID is not found, "
                "a 404 error will be returned.",
    responses={
        404: {
            "description": "Movie not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given id was not found."}
                }
            }
        }
    }
)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_postgres_db)
) -> MovieDetailResponseSchema:
    request = select(MovieModel).options(
        joinedload(MovieModel.certification),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.stars),
        joinedload(MovieModel.directors)
    ).where(MovieModel.id == movie_id)

    response = await db.execute(request)
    movie = response.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return MovieDetailResponseSchema.model_validate(movie)


@router.delete("movies/{movie_id}/",
             summary="Delete movie with the given ID",
             description="Delete the specific movie from the database with the given ID."
                         "If the movie exist, it will be deleted. if it does not exist, "
                         "a 404 error will e return.",
             responses={
                 200: {"description": "Movie deleted successfully."},
                 404: {
                     "description": "Movie not found",
                     "content": {
                         "application/json": {
                             "example": {"detail": "Movie with the given ID was not found."}
                         }
                     }
                 }
             }
             )
async def delete_movie_by_id(
        movie_id: int,
        db:AsyncSession = Depends(get_postgres_db)
):
    request = select(MovieModel).where(MovieModel.id == movie_id)
    response = await db.execute(request)
    movie = response.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}


@router.patch("/movies/{movie_id}/",
              response_model=MovieUpdateResponseSchema,
              summary="Update movie by the given ID.",
              description="Update details of a specific movie by its unique ID."
                          "This endpoint updates the details of an existing movie. If the movie with "
                          "the given ID does not exist, a 404 error is returned.",
              responses={
                  200: {
                      "description": "Movie updated successfully.",
                      "content": {
                          "application/json": {
                              "example": {"detail": "Movie update successfully."}
                          }
                      }
                  },
                  404: {
                      "description": "Movie not found",
                      "content": {
                          "application/json": {
                              "example": {"detail": "Movie with the given ID was not found."}
                          }
                      },
                  },
              }
)
async def update_movie_by_id(movie_id: int, movie_data: MovieUpdateResponseSchema, db: AsyncSession = Depends(get_postgres_db)):
    request = select(MovieModel).where(MovieModel.id == movie_id)
    response = await db.execute(request)
    movie = response.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
