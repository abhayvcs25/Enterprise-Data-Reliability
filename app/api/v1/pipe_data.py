from fastapi import APIRouter,Depends

from app.repositories.pipe_data_repo import PipeDataRepo
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.dataSource_repo import DataSourceRepo

from app.services.pipe_data_service import PipelineDataSourceServices

from app.schemas.pipe_data_DTO import Pipe_Data_Responce,Pipe_Data_Update,Pipe_Data_Create

from app.db.db import get_db

from sqlalchemy.orm import Session

from typing import List

Pipe_Data_Router = APIRouter()

def get_pipe_data_services(db:Session = Depends(get_db))->PipelineDataSourceServices:
    pipe_repo = PipelineRepository(db)
    data_Source_repo = DataSourceRepo(db)
    pipe_data_repo = PipeDataRepo(db)

    return PipelineDataSourceServices(data_Source_repo,pipe_data_repo,pipe_repo)

@Pipe_Data_Router.get("",response_model=List[Pipe_Data_Responce])
def get_all(service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.get_all()

@Pipe_Data_Router.get("/{pipe_data_id}",response_model=Pipe_Data_Responce)
def get_by_id(pipe_data_id:int,service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.get_by_id(pipe_data_id)

@Pipe_Data_Router.get("/pipeline/{pipe_id}",response_model=List[Pipe_Data_Responce])
def get_by_pipe_id(pipe_id:int,service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.get_by_pipe_id(pipe_id)

@Pipe_Data_Router.get("/datasource/{data_id}",response_model=List[Pipe_Data_Responce])
def get_by_data_id(data_id:int,service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.get_by_data_id(data_id)

@Pipe_Data_Router.post("",response_model=Pipe_Data_Responce)
def create(pipe_data:Pipe_Data_Create,service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.create(pipe_data)

@Pipe_Data_Router.delete("/{pipe_data_id}")
def delete(pipe_data_id:int,service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.delete(pipe_data_id)

@Pipe_Data_Router.put("/{pipe_data_id}",response_model=Pipe_Data_Responce)
def update(pipe_data_id:int,data:Pipe_Data_Update,service:PipelineDataSourceServices = Depends(get_pipe_data_services)):
    return service.update(pipe_data_id=pipe_data_id,data=data)