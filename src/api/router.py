from fastapi import APIRouter

from src.api.v1.chat import router as chat_router

routers = APIRouter()

routers_list = [chat_router]
for router in routers_list:
    router.tags = ["v1"]
    routers.include_router(router)
