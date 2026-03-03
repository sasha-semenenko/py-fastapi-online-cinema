import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.models.base import Base
from src.config import settings

from src.models.accounts import UserModel, UserProfileModel
from src.models.movies import MovieModel, MovieDirectorsModel, MovieGenresModel, MovieStarsModel
from src.models.shopping_cart import CartModel, CartItemModel
from src.models.order import OrderModel, OrderItemModel


meta = MetaData()
async_engine = create_async_engine(url=settings.POSTGRES_URL, echo=True)

AsyncLocalSession = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_postgres_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncLocalSession() as session:
        yield session


@asynccontextmanager
async def get_postgresql_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session using a context manager.

    This function allows for managing the database session within a `with` statement.
    It ensures that the session is properly initialized and closed after execution.

    :return: An asynchronous generator yielding an AsyncSession instance.
    """
    async with AsyncLocalSession() as session:
        yield session

#
# asyncio.run(init_db())