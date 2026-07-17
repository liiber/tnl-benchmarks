import asyncio

from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from alembic import command
from src.environment import ENV

DB_URL = f"postgresql+asyncpg://{ENV.DB_USER}:{ENV.DB_PASSWORD}@{ENV.DB_HOST}:{ENV.DB_PORT}/{ENV.DB_NAME}"

DB_CONNECT_RETRIES = 10
DB_CONNECT_RETRY_DELAY_SECONDS = 2


async_engine = create_async_engine(DB_URL, echo=False, future=True)

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


def _run_migrations_sync() -> None:
    alembic_cfg = Config("alembic.ini")
    try:
        command.upgrade(alembic_cfg, "head")
    except CommandError:
        # Stale revision ID (e.g. migrations were reset). Clear and retry.
        command.stamp(alembic_cfg, "base")
        command.upgrade(alembic_cfg, "head")


async def _check_db_connection() -> None:
    async with async_engine.connect():
        pass


async def wait_for_db() -> None:
    for attempt in range(DB_CONNECT_RETRIES):
        try:
            await _check_db_connection()
        except Exception as exc:
            print(f"Database not ready ({attempt + 1}/{DB_CONNECT_RETRIES}): {exc}")
            await asyncio.sleep(DB_CONNECT_RETRY_DELAY_SECONDS)
            continue
        await asyncio.to_thread(_run_migrations_sync)
        return
    raise RuntimeError("Database failed to start")


async def get_async_db():
    async with async_session() as session:
        yield session
