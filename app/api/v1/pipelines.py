from fastapi import APIRouter,Depends
from app.schemas.PipelinesDto import PipelineCreate,PipelineResponse
from app.services.pipelines_services import PipelineService
from app.repositories.pipeline_repo import PipelineRepository
from sqlalchemy.orm import Session
from app.db.db import get_db
from typing import List

Pipeline_Router = APIRouter()


def get_pipeline_service(db: Session = Depends(get_db)) -> PipelineService:
    repository = PipelineRepository(db)

    return PipelineService(repository)


@Pipeline_Router.get("/pipelines",response_model=List[PipelineResponse])
def Pipelines_get(service:PipelineService = Depends(get_pipeline_service)):
    return service.get_all_pipelines()

@Pipeline_Router.get("/pipelines/{pipe_id}",response_model=PipelineResponse)
def Pipeline_get_by_id(pipe_id: int, service : PipelineService = Depends(get_pipeline_service)):
    return service.get_pipeline_by_id(pipe_id)

@Pipeline_Router.post("/pipelines",response_model=PipelineResponse)
def Pipeline_post(data:PipelineCreate,service:PipelineService = Depends(get_pipeline_service)):
    return service.create_pipeline(data)

@Pipeline_Router.put("/pipelines/{id}")
def Pipeline_update(id:int):
    pass

@Pipeline_Router.delete("/pipelines/{id}")
def Pipeline_delete(id:int):
    pass