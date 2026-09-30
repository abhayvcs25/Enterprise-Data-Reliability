from app.models.pipe_dataSource_M_M_relation import PipelineDataSourceModel
from sqlalchemy.orm import Session
from app.schemas.pipe_data_DTO import Pipe_Data_Create,Pipe_Data_Update

class PipeDataRepo:
    def __init__(self,db:Session):
        self.db = db

    def create(self,data:Pipe_Data_Create):
        data_source = PipelineDataSourceModel(
            pipeline_id = data.pipeline_id,
            datasource_id = data.datasource_id,
            execution_order = data.execution_order
        )

        self.db.add(data_source)
        self.db.commit()
        self.db.refresh(data_source)
        return data_source

    def get_all_pds(self):
        return self.db.query(PipelineDataSourceModel).all()

    def get_by_id(self,pipe_data_id:int):
        return self.db.query(PipelineDataSourceModel).filter(PipelineDataSourceModel.id == pipe_data_id).first()

    def get_by_Pipe_id(self,pipe_id:int):
        return self.db.query(PipelineDataSourceModel).filter(PipelineDataSourceModel.pipeline_id == pipe_id).order_by(PipelineDataSourceModel.execution_order).first()

    def get_by_Data_id(self,data_id:int):
        return self.db.query(PipelineDataSourceModel).filter(PipelineDataSourceModel.datasource_id == data_id).order_by(PipelineDataSourceModel.execution_order).first()

    def get_by_pipe_data_id(self,pipe_id:int,data_id:int):
        return self.db.query(PipelineDataSourceModel).filter(PipelineDataSourceModel.pipeline_id == pipe_id , PipelineDataSourceModel.datasource_id == data_id).first()

    def delete(self,data_source:PipelineDataSourceModel):
        self.db.delete(data_source)
        self.db.commit()
        return data_source

    def update_pipe_data(self,data_source:PipelineDataSourceModel,data:Pipe_Data_Update):
        data_source.execution_order = data.execution_order

        self.db.commit()
        self.db.refresh(data_source)
        
        return data_source
