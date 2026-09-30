from pydantic import BaseModel,ConfigDict

class Pipe_Data_Create(BaseModel):
    pipeline_id :int
    datasource_id :int
    execution_order :int

class Pipe_Data_Responce(BaseModel):
    id:int
    pipeline_id :int
    datasource_id :int
    execution_order :int
    model_config = ConfigDict(from_attributes=True)

class Pipe_Data_Update(BaseModel):
    # pipeline_id :int
    # datasource_id :int
    execution_order :int