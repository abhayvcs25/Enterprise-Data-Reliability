from pydantic import BaseModel,ConfigDict
from datetime import datetime
from app.models.pipelines import PipelineStatus


class PipelineCreate(BaseModel):
    name : str
    description : str | None = None
    status : PipelineStatus = PipelineStatus.PENDING

class PipelineResponse(BaseModel):
    id : int
    name : str
    description : str | None = None
    status : PipelineStatus 
    created_at : datetime
    updated_at : datetime

    model_config = ConfigDict(from_attributes=True)
