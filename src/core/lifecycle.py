from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.client import close_connection, open_connection


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    open_connection()
    try:
        yield
    finally:
        await close_connection()
