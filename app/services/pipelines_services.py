# from db.db import get_db
# from models.pipelines import PipelinesModel
from app.schemas.PipelinesDto import PipelineCreate
from app.repositories.pipeline_repo import PipelineRepository

class PipelineService:
    def __init__(self,repository:PipelineRepository):
        self.repository = repository

    def create_pipeline(self,data:PipelineCreate):
        return self.repository.create(data)

    def get_all_pipelines(self):
        return self.repository.get_all()