from fastapi import APIRouter,Depends
from app.schemas.PipelinesDto import PipelineCreate,PipelineResponse,PipelineUpdate
from app.schemas.PipelineRunDto import PipelineRunResponse
from app.services.pipelines_services import PipelineService
from app.services.pipelineRun_services import PipelineExecutionService
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from sqlalchemy.orm import Session
from app.db.db import get_db
from typing import List

Pipeline_Router = APIRouter()


def get_pipeline_service(db: Session = Depends(get_db)) -> PipelineService:
    repository = PipelineRepository(db)

    return PipelineService(repository)

def get_pipeline_execution_service(
    db: Session = Depends(get_db)
) -> PipelineExecutionService:

    pipeline_repository = PipelineRepository(db)
    pipeline_run_repository = PipelineRunRepositroy(db)

    return PipelineExecutionService(
        pipeline_repository,
        pipeline_run_repository
    )


@Pipeline_Router.get("/pipelines",response_model=List[PipelineResponse])
def Pipelines_get(service:PipelineService = Depends(get_pipeline_service)):
    return service.get_all_pipelines()

@Pipeline_Router.get("/pipeline-runs",response_model=List[PipelineRunResponse])
def get_runs(service:PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.get_all_run()

@Pipeline_Router.get("/pipelines/{pipe_id}",response_model=PipelineResponse)
def Pipeline_get_by_id(pipe_id: int, service : PipelineService = Depends(get_pipeline_service)):
    return service.get_pipeline_by_id(pipe_id)

@Pipeline_Router.post("/pipelines",response_model=PipelineResponse)
def Pipeline_post(data:PipelineCreate,service:PipelineService = Depends(get_pipeline_service)):
    return service.create_pipeline(data)

@Pipeline_Router.put("/pipelines/{id}",response_model=PipelineResponse)
def Pipeline_update(id:int,data:PipelineUpdate,service:PipelineService = Depends(get_pipeline_service)):
    return service.update_pipeline_by_id(id,data)

@Pipeline_Router.delete("/pipelines/{id}",response_model=PipelineResponse)
def Pipeline_delete(id:int,service: PipelineService = Depends(get_pipeline_service)):
    return service.delete_pipeline_by_id(id)

@Pipeline_Router.post("/pipelines/{pipeline_id}/run",response_model=PipelineRunResponse)
def Create_Pipeline_Run(pipeline_id:int,service:PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.run_pipeline(pipeline_id)

@Pipeline_Router.get("/pipelines/{pipeline_id}/runs",response_model=List[PipelineRunResponse])
def Get_pipeline_runs(pipeline_id:int,service: PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.get_pipeline_runs(pipeline_id)

@Pipeline_Router.get("/pipeline-runs/{run_id}",response_model=PipelineRunResponse)
def Get_runs_byid(run_id:int,service: PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.get_run(run_id)


# POST /api/v1/pipelines/{pipeline_id}/run
# GET  /api/v1/pipelines/{pipeline_id}/runs
# GET  /api/v1/pipeline-runs/{run_id}