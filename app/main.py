from fastapi import FastAPI
# from utils.settings import settings

from app.api.v1.health import health_router
from app.api.v1.pipelines import Pipeline_Router

# from db.db import Base,engine

# Base.metadata.create_all(bind=engine)

app=FastAPI()

app.include_router(health_router,prefix="/api/v1")
app.include_router(Pipeline_Router,prefix="/api/v1")