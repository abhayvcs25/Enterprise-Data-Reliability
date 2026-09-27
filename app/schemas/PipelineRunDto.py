from pydantic import BaseModel,ConfigDict
from datetime import datetime

from app.models.pipelines import PipelineStatus


class PipelineRunCreate(BaseModel):
    pipeline_id:int

class PipelineRunResponse(BaseModel):
    id:int
    pipeline_id:int
    status : PipelineStatus
    started_at:datetime|None = None
    finished_at:datetime | None = None
    duration:float | None = None
    error_message:str | None = None

    model_config = ConfigDict(from_attributes=True)

