from schemas.examples.movies import movie_list_item_schema, genre_schema_example

user_schema = {
    "id": 1,
    "email": "example@email.com",
    "password": "<PASSWORD>",
}


cart_schema = {
    "id": 1,
    "user_id": user_schema
}


movie_cart_list_item_schema = {
    "id": 1,
    "name": "Movie Item",
    "year": 2025,
    "time": 205,
    "imdb": 3.4,
    "votes": 3,
    "meta_score": 1.2,
    "gross": 2.4,
    "description": "Some Test for movie items test list",
    "price": 3.6,
    "genres": genre_schema_example
}


cart_item_list_schema = {
    "cart_id": cart_schema,
    "movies": [movie_cart_list_item_schema]
}
