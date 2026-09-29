from fastapi import APIRouter,Depends,status

from app.schemas.datasourceDto import DataSourceResponse,DataSourceUpdate,DataSourceCreate
from app.repositories.dataSource_repo import DataSourceRepo
from app.services.dataSource_service import DataSourceServices

from app.db.db import get_db

from typing import List
from sqlalchemy.orm import Session


DataSource_Router = APIRouter()

# for adding the sessin to the repo class
def get_dataSource_services(db: Session = Depends(get_db)) -> DataSourceServices:
    data_repo = DataSourceRepo(db)
    return DataSourceServices(data_repo)


#to get all DS(data source)
@DataSource_Router.get("",response_model= List[DataSourceResponse])
def get_all(service:DataSourceServices = Depends(get_dataSource_services)):
    return service.get_all_data_source()

#to get 1 DS
@DataSource_Router.get("/{data_s_id}",response_model=DataSourceResponse)
def get_by_id(data_s_id:int,service:DataSourceServices = Depends(get_dataSource_services)):
    return service.get_data_source_by_id(data_s_id)

#to create DS
@DataSource_Router.post("",response_model=DataSourceResponse,
                        status_code=status.HTTP_201_CREATED)
def create_data_source(data:DataSourceCreate,service:DataSourceServices = Depends(get_dataSource_services)):
    return service.create_data_source(data)

#to update DS
@DataSource_Router.put("/{data_s_id}",response_model=DataSourceResponse)
def update(data_s_id:int,Update_data:DataSourceUpdate,service: DataSourceServices = Depends(get_dataSource_services)):
    return service.update_data_source(data_s_id,Update_data)

# to delete DS
@DataSource_Router.delete("/{data_s_id}",status_code=status.HTTP_200_OK)
def delete(data_s_id:int,service:DataSourceServices= Depends(get_dataSource_services)):
    return service.delete_data_source(data_s_id)

#to get the location from DS and perfrom operations on it and give the result
@DataSource_Router.get("/{data_s_id}/run")
def Run_csv(data_s_id:int,service:DataSourceServices = Depends(get_dataSource_services)):
    return service.ingest_data_s(data_s_id)