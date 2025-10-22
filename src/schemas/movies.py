from typing import List, Text, Optional

from pydantic import BaseModel, Field
import uuid

from schemas.examples.movies import genre_schema_example, star_schema_example, director_schema_example, \
    certification_schema_example, movie_create_schema_example, movie_detail_schema_example, movie_list_item_schema, \
    movie_list_response_schema, movie_update_schema


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                genre_schema_example
            ]
        }
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                star_schema_example
            ]
        }
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                director_schema_example
            ]
        }
    }


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                certification_schema_example
            ]
        }
    }


class MovieSchema(BaseModel):

    name: str = Field(..., max_length=255)
    year: int
    time: int
    imdb: float = Field(..., ge=0)
    votes: int
    meta_score: float = Field(..., ge=0)
    gross: float = Field(..., ge=0)
    description: str
    price: float = Field(..., ge=0)

    model_config = {
        "from_attributes": True
    }


class MovieCreateSchema(BaseModel):

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., max_length=255)
    year: int
    time: int
    imdb: float = Field(..., ge=0)
    votes: int
    meta_score: float = Field(..., ge=0)
    gross: float = Field(..., ge=0)
    description: Text
    price: float = Field(..., ge=0)
    certification: str
    genres: List[str]
    stars: List[str]
    directors: List[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_create_schema_example
            ]
        }
    }

class MovieDetailResponseSchema(MovieSchema):

    id: int
    uuid: uuid.UUID
    certification: CertificationSchema
    genres: List[GenreSchema]
    stars: List[StarSchema]
    directors: List[DirectorSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_detail_schema_example
            ]
        }
    }


class MovieListItemSchema(BaseModel):
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

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_list_item_schema
            ]
        }
    }



class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
        "json_response_schema": [
            movie_list_response_schema
        ]
    }


class MovieUpdateResponseSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = Field(None, ge=0)
    votes: Optional[int] = None
    meta_score: Optional[float] = Field(None, ge=0)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[Text] = None
    price: Optional[float] = Field(None, ge=0)

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            movie_update_schema
        }
    }
