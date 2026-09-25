from fastapi import APIRouter,Depends
from app.schemas.PipelinesDto import PipelineCreate,PipelineResponse
from app.services.pipelines_services import PipelineService
from app.repositories.pipeline_repo import PipelineRepository
from sqlalchemy.orm import Session
from app.db.db import get_db

Pipeline_Router = APIRouter()


def get_pipeline_service(db: Session = Depends(get_db)) -> PipelineService:
    repository = PipelineRepository(db)

    return PipelineService(repository)


@Pipeline_Router.get("/pipelines")
def PipelinesGet():
    pass

@Pipeline_Router.get("/pipelines/{id}")
def PipelineGet(id:int):
    pass

@Pipeline_Router.post("/pipelines",response_model=PipelineResponse)
def PipelinePost(data:PipelineCreate,service:PipelineService = Depends(get_pipeline_service)):
    return service.create_pipeline(data)

@Pipeline_Router.put("/pipelines/{id}")
def PipelineUpdate(id:int):
    pass

@Pipeline_Router.delete("/pipelines/{id}")
def PipelineDelete(id:int):
    pass