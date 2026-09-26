# from db.db import get_db
# from models.pipelines import PipelinesModel
from app.schemas.PipelinesDto import PipelineCreate,PipelineUpdate
from app.repositories.pipeline_repo import PipelineRepository
from fastapi import HTTPException
class PipelineService:
    def __init__(self,repository:PipelineRepository):
        self.repository = repository

    def create_pipeline(self,data:PipelineCreate):
        return self.repository.create(data)

    def get_all_pipelines(self):
        return self.repository.get_all()

    def get_pipeline_by_id(self, pipe_id: int):
        pipeline = self.repository.get_by_id(pipe_id)

        if pipeline is None:
            raise HTTPException(status_code=404,detail="pipeline not found")

        return pipeline

    def update_pipeline_by_id(self,pipe_id: int, body: PipelineUpdate):
        pipeline = self.repository.update_pipeline(pipe_id,body)

        if pipeline is None:
            raise HTTPException(status_code= 404,detail="pipeline not found")

        return pipeline

    def delete_pipeline_by_id(self,pipe_id: int):
            pipeline = self.repository.delete_pipeline(pipe_id)
    
            if pipeline is None:
                raise HTTPException(status_code= 404,detail="pipeline not found")
    
            return pipeline
    