from app.schemas.pipe_data_DTO import Pipe_Data_Update,Pipe_Data_Create
from app.repositories.pipe_data_repo import PipeDataRepo
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.dataSource_repo import DataSourceRepo
from fastapi import HTTPException



class PipelineDataSourceServices:
    def __init__(self,data_Source_repo:DataSourceRepo,pipe_data_repo:PipeDataRepo,pipe_repo:PipelineRepository):
        self.pipe_repo = pipe_repo
        self.data_Source_repo = data_Source_repo
        self.pipe_data_repo = pipe_data_repo
        

    def create(self,pipe_data:Pipe_Data_Create):
        pipeline = self.pipe_repo.get_by_id(pipe_data.pipeline_id)
        if pipeline is None:
            raise HTTPException(status_code=404,detail="Pipeline id not found")

        pipeline = self.data_Source_repo.get_by_id(pipe_data.datasource_id)
        if pipeline is None:
            raise HTTPException(status_code=404,detail="DataSource id not found")

        pipe_data_source = self.pipe_data_repo.get_by_pipe_data_id(pipe_data.pipeline_id,pipe_data.datasource_id)
        if pipe_data_source:
            raise HTTPException(status_code=409,detail="connection already exists cannot create this connection")

        if pipe_data.execution_order < 1:
            raise HTTPException(status_code=400,detail="Execution order can't be less then 1")

        return self.pipe_data_repo.create(pipe_data)

    def get_by_id(self,pipe_data_id:int):
        pipe_data = self.pipe_data_repo.get_by_id(pipe_data_id)
        if pipe_data is None:
            raise HTTPException(status_code=404,detail="pipeline datasource id not found")
        return pipe_data

    def get_all(self):
        return self.pipe_data_repo.get_all_pds()
        

    def get_by_data_id(self,data_id:int):
        pipe_data = self.pipe_data_repo.get_by_Data_id(data_id)
        if not pipe_data:
            raise HTTPException(status_code=404,detail="data id is not associated")
        return pipe_data

    def get_by_pipe_id(self,pipe_id:int):
        pipe_data = self.pipe_data_repo.get_by_Pipe_id(pipe_id)
        if not pipe_data:
            raise HTTPException(status_code=404,detail="pipe id is not associated")
        return pipe_data

    def update(self,pipe_data_id:int,data:Pipe_Data_Update):
        pipe_data = self.pipe_data_repo.get_by_id(pipe_data_id)
        if pipe_data is None:
            raise HTTPException(status_code=404,detail="pipeline dataSource id is not associated")

        if data.execution_order < 1:
            raise HTTPException(status_code=400,detail="Execution order can't be less then 1")
        
        return self.pipe_data_repo.update_pipe_data(pipe_data,data)

    def delete(self,pipe_data_id:int):
        pipe_data = self.pipe_data_repo.get_by_id(pipe_data_id)
        if pipe_data is None:
            raise HTTPException(status_code=404,detail="pipeline datasource id not found")

        self.pipe_data_repo.delete(pipe_data)

        return {
                    "message":"Pipeline DataSource deleted successfully"
                }
    
        