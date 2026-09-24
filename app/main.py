from fastapi import FastAPI
from api.v1.health import health_router
from db.db import Base,engine
from utils.settings import settings



Base.metadata.create_all(bind=engine)

app=FastAPI()

app.include_router(health_router,prefix="/api/v1")