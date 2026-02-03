from __future__ import annotations
from typing import List, TYPE_CHECKING

from src.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer,
    String,
    Float,
    Text,
    DECIMAL,
    ForeignKey,
    UniqueConstraint,
    Table,
    Column,
    types,
    Boolean
)

if TYPE_CHECKING:
    from src.models.shopping_cart import CartItemModel


MovieGenresModel = Table(
    "movie_genres",
    Base.metadata, Column(
        "movie_id",
        ForeignKey("movies_table.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "genre_id",
        Base.metadata,
        ForeignKey("genres_table.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    extend_existing=True
)


MovieStarsModel = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id",
           ForeignKey("movies_table.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("stars_id",
           ForeignKey("stars_table.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    extend_existing=True
)


MovieDirectorsModel = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id",
           ForeignKey("movies_table.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("director_id",
           ForeignKey("directors_table.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    extend_existing=True
)

class GenreModel(Base):
    __tablename__ = "genres_table"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieGenresModel,
        back_populates="genres"
    )

    def __repr__(self):
        return f"Genre(name={self.name})"


class StarModel(Base):
    __tablename__ = "stars_table"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieStarsModel,
        back_populates="stars"
    )

    def __repr__(self):
        return f"<Star(name={self.name})>"


class DirectorModel(Base):
    __tablename__="directors_table"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieDirectorsModel,
        back_populates="directors"
    )

    def __repr__(self):
        return f"<Director(name={self.name})>"


class CertificationModel(Base):
    __tablename__="certifications_table"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="certification")

    def __repr__(self):
        return f"<Certification(name={self.name})>"

class MovieModel(Base):
    __tablename__="movies_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(types.Uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[float] = mapped_column(Float, nullable=True)
    gross: Mapped[float] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)

    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications_table.id"), nullable=False)
    certification: Mapped["CertificationModel"] = relationship("CertificationModel", back_populates="movies")

    cart_item: Mapped[list["CartItemModel"]] = relationship(back_populates="movie")
    purchased: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel",
        secondary=MovieGenresModel,
        back_populates="movies"
    )

    stars: Mapped[list["StarModel"]] = relationship(
        "StarModel",
        secondary=MovieStarsModel,
        back_populates="movies"
    )

    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel",
        secondary=MovieDirectorsModel,
        back_populates="movies"
    )

    __table_args__ = (UniqueConstraint("name", "year", "time", name="unique_movie_constraints"), {"extend_existing": True})

    @classmethod
    def default_order_by(cls):
        return[cls.id.desc()]

    def __repr__(self):
        return f"<Movie(name='{self.name}', release_year='{self.year}', score={self.meta_score})>"
