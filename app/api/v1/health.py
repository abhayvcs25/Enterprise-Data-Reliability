from fastapi import APIRouter
from app.controller.v1.health import health_check



health_router=APIRouter()

@health_router.get("/health")
def health():
    return health_check()