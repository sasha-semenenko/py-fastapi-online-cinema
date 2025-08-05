from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from models.accounts import Base
from src.config import settings


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


async def get_postgres_db():
    async with AsyncLocalSession() as session:
        yield session
