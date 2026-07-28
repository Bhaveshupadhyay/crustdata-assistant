import urllib.parse

from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from upstash_redis.asyncio import Redis

from src.core.settings import settings

_postgres_client: sessionmaker | None = None
_redis_client: Redis | None = None
_qdrant_client: QdrantClient | None = None
Base = declarative_base()


def get_postgres_client() -> sessionmaker:
    global _postgres_client
    if _postgres_client is None:
        username = settings.POSTGRES_USERNAME
        raw_password = settings.POSTGRES_DB_PASSWORD
        encoded_password = urllib.parse.quote_plus(raw_password)
        db_host = settings.POSTGRES_DB_HOST

        sqlalchemy_database_url = (
            f"postgresql://{username}:{encoded_password}@{db_host}:5432/postgres?sslmode=require"
        )

        engine = create_engine(sqlalchemy_database_url)
        _postgres_client = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _postgres_client


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN,
        )
    return _redis_client


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=settings.QDRANT_ENDPOINT,
            api_key=settings.QDRANT_KEY,
        )
    return _qdrant_client


def open_connection() -> None:
    get_redis_client()
    get_postgres_client()


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def close_postgres_client() -> None:
    global _postgres_client
    if _postgres_client is not None:
        _postgres_client.close_all()
        _postgres_client = None


async def close_connection() -> None:
    await close_redis_client()
    close_postgres_client()
