from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from src.environment import ENV

DB_URL = f"postgresql+asyncpg://{ENV.DB_USER}:{ENV.DB_PASSWORD}@{ENV.DB_HOST}:{ENV.DB_PORT}/{ENV.DB_NAME}"

async_engine = create_async_engine(DB_URL, echo=True, future=True)
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def init_db():
    """Async tables creation"""
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_async_db():
    async with async_session() as session:
        yield session