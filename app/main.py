from fastapi import FastAPI
from api.v1.health import health_router


app=FastAPI()

app.include_router(health_router,prefix="/api/v1")