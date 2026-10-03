from fastapi import APIRouter,Depends

from app.schemas.PipelinesDto import PipelineCreate,PipelineResponse,PipelineUpdate
from app.schemas.PipelineRunDto import PipelineRunResponse
from app.schemas.ingestionDto import IngestionResponse,IngestionErrorResponse

from app.services.pipelines_services import PipelineService
from app.services.pipelineRun_services import PipelineExecutionService

from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from app.repositories.pipe_data_repo import PipeDataRepo
from app.repositories.dataSource_repo import DataSourceRepo

from app.db.db import get_db

from sqlalchemy.orm import Session
from typing import List,Union

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



def get_pipeline_execution_service(
    db: Session = Depends(get_db)
) -> PipelineExecutionService:

    pipeline_repository = PipelineRepository(db)
    pipeline_run_repository = PipelineRunRepositroy(db)
    datasource_repository = DataSourceRepo(db=db)
    pipe_data_repo = PipeDataRepo(db=db)
    return PipelineExecutionService(
        pipeline_repository,
        pipeline_run_repository,
        datasource_repository,
        pipe_data_repo
    )

##these are the apis to CURD oprations for piplines

#this is to get all pipelines 
@Pipeline_Router.get("/pipelines",response_model=List[PipelineResponse])
def Pipelines_get(service:PipelineService = Depends(get_pipeline_service)):
    return service.get_all_pipelines()

#this is to 1 pipeline
@Pipeline_Router.get("/pipelines/{pipe_id}",response_model=PipelineResponse)
def Pipeline_get_by_id(pipe_id: int, service : PipelineService = Depends(get_pipeline_service)):
    return service.get_pipeline_by_id(pipe_id)

# this is to create a pipeline
@Pipeline_Router.post("/pipelines",response_model=PipelineResponse)
def Pipeline_post(data:PipelineCreate,service:PipelineService = Depends(get_pipeline_service)):
    return service.create_pipeline(data)

# this is to update a pipeline
@Pipeline_Router.put("/pipelines/{id}",response_model=PipelineResponse)
def Pipeline_update(id:int,data:PipelineUpdate,service:PipelineService = Depends(get_pipeline_service)):
    return service.update_pipeline_by_id(id,data)

# this to delete a pipeline
@Pipeline_Router.delete("/pipelines/{id}",response_model=PipelineResponse)
def Pipeline_delete(id:int,service: PipelineService = Depends(get_pipeline_service)):
    return service.delete_pipeline_by_id(id)



### these are the apis to runs the pipelines

#this is to make the pipeline run 
@Pipeline_Router.post("/pipelines/{pipeline_id}/run",response_model=Union[IngestionResponse,IngestionErrorResponse])
def Create_Pipeline_Run(pipeline_id:int,service:PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.run_pipeline(pipeline_id)

# this is to get runs of a list of pipeline id
@Pipeline_Router.get("/pipelines/{pipeline_id}/runs",response_model=List[PipelineRunResponse])
def Get_pipeline_runs(pipeline_id:int,service: PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.get_pipeline_runs(pipeline_id)

# this is to get run a specific run
@Pipeline_Router.get("/pipeline-runs/{run_id}",response_model=PipelineRunResponse)
def Get_runs_byid(run_id:int,service: PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.get_run(run_id)

# this is to get all runs
@Pipeline_Router.get("/pipeline-runs",response_model=List[PipelineRunResponse])
def get_runs(service:PipelineExecutionService = Depends(get_pipeline_execution_service)):
    return service.get_all_run()



# POST /api/v1/pipelines/{pipeline_id}/run
# GET  /api/v1/pipelines/{pipeline_id}/runs
# GET  /api/v1/pipeline-runs/{run_id}