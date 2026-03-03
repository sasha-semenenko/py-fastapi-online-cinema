certification_schema_example = {
    "id": 1,
    "name": "New Certification",
}

genre_schema_example = {
    "id": 1,
    "name": "Genre"
}

star_schema_example = {
    "id": 1,
    "name": "Star"
}

director_schema_example = {
    "id": 1,
    "name": "Director"
}


movie_create_schema_example = {
    "name": "John Wick",
    "year": 2022,
    "time": 168,
    "imdb": 1.9,
    "votes": 5,
    "meta_score": 3.5,
    "gross": 3.9,
    "description": "This movie about killing people",
    "price": 325.6,
    "certification": "New Certification",
    "genres": ["Genre"],
    "stars": ["Star"],
    "directors": ["Director"]
}

movie_detail_schema_example = {
    "id": 1,
    "votes": 5,
    "gross": 3.6,
    "price": 135.6,
    "certification": certification_schema_example,
    "genres": genre_schema_example,
    "stars": star_schema_example,
    "directors": director_schema_example
}

movie_list_item_schema = {
    "id": 1,
    "name": "Movie Item",
    "year": 2025,
    "time": 205,
    "imdb": 3.4,
    "votes": 3,
    "meta_score": 1.2,
    "gross": 2.4,
    "description": "Some Test for movie items test list",
    "price": 3.6
}

movie_list_response_schema = {
    "movies": [movie_list_item_schema],
    "prev_page": "movies/movies-list/?page=1&per_page=1",
    "next_page": "movies/movies-list/?page=3&per_page=1",
    "total_pages": 100,
    "total_items": 100
}

movie_update_schema = {
    "name": "Updated Movie",
    "year": 4045,
    "time": 25,
    "imdb": 0.4,
    "votes": 5,
    "meta_score": 3.5,
    "gross": 2.6,
    "description": "Some description for movie create schema",
    "price": 125.6
}
