import pytest

from sqlalchemy import select

from models.movies import GenreModel, StarModel, DirectorModel, CertificationModel, MovieModel


@pytest.mark.asyncio
async def test_movies_empty_database(client, db_session):
    response = await client.get("movies/movies-list")
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"

    expected_detail = {"detail": "Not Found"}
    assert response.json() == expected_detail, f"Expected: {expected_detail}, got {response.json()}"


@pytest.mark.asyncio
async def test_create_movie(client, db_session):
    default = {
        "name": "One Movie",
        "year": 2037,
        "time": 436,
        "imdb": 4.3,
        "votes": 4,
        "meta_score": 4.5,
        "gross": 4.6,
        "description": "Some description for movie create schema",
        "price": 147.6,
        "certification": "One Certification",
        "genres": ["One Comedy", "One Horror"],
        "stars": ["One North", "One West"],
        "directors": ["One First", "One Second"]
    }

    response = await client.post("movies/create/", json=default)
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"

    response_data = response.json()
    assert default["name"] == response_data["name"], "Movie name dose not match"
    assert default["year"] == response_data["year"], "Movie year dose not match"
    assert default["time"] == response_data["time"], "Movie time dose not match"
    assert default["votes"] == response_data["votes"], "Movie votes dose not match"

    for genre_name in default["genres"]:
        request = select(GenreModel).where(GenreModel.name == genre_name)
        response = await db_session.execute(request)
        genre = response.scalars().first()
        assert genre is not None, f"Genre {genre_name} was not created."

    for star_name in default["stars"]:
        request = select(StarModel).where(StarModel.name == star_name)
        response = await db_session.execute(request)
        stars = response.scalars().first()
        assert stars is not None, f"Star {star_name} was not created."

    for director_name in default["directors"]:
        request = select(DirectorModel).where(DirectorModel.name == director_name)
        response = await db_session.execute(request)
        director = response.scalars().first()
        assert director is not None, f"Director {director_name} was not created."

    request = select(CertificationModel).where(CertificationModel.name == default["certification"])
    response = await db_session.execute(request)
    certification = response.scalars().first()
    assert certification is not None, f"Certification {default['certification']} was not created."


@pytest.mark.asyncio
async def test_delete_movie_success(client, db_session):
    request = select(MovieModel).limit(1)
    response = await db_session.execute(request)
    movie = response.scalars().first()
    assert movie is not None, "Expected no movies found in the database to delete."

    movie_id = movie.id

    response = await client.delete(f"movies/movie/{movie_id}/")
    assert response.status_code == 204, f"Expected status code 204, but got {response.status_code}"

    request = select(MovieModel).where(MovieModel.id == movie_id)
    response = await db_session.execute(request)
    deleted_movie = response.scalars().first()
    assert deleted_movie is None, f"Movie with ID {deleted_movie.id} was deleted."


@pytest.mark.asyncio
async def test_update_movie_success(client, db_session):
    request = select(MovieModel).limit(1)
    response = await db_session.execute(request)
    movie = response.scalars().first()
    assert movie is not None, "No movies found in the database to update."

    to_update = {
        "name": "Updated name",
        "time": 300
    }

    movie_id = movie.id

    response = await client.patch(f"movies/movie/{movie_id}/", json=to_update)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    response_data = response.json()
    assert response_data["detail"] == "Movie updated successfully.", (
        f"Expected detail message: 'Movie updated successfully.', but got: {response_data['detail']}"
    )

    await db_session.rollback()

    stmt_check = select(MovieModel).where(MovieModel.id == movie_id)
    result_check = await db_session.execute(stmt_check)
    updated_movie = result_check.scalars().first()

    assert updated_movie.name == to_update["name"], "Movie name was not updated."
    assert updated_movie.time == to_update["time"], "Movie time was not updated."
