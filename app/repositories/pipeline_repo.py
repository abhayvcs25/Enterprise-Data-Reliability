from sqlalchemy.orm import Session
from app.models.pipelines import PipelinesModel
from app.schemas.PipelinesDto import PipelineCreate,PipelineUpdate



class PipelineRepository:
    def __init__(self,db: Session):
        self.db = db

    def create(self,data: PipelineCreate):
        pipeline= PipelinesModel(
            name= data.name,
            description= data.description,
            status= data.status
        )

        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline


    def get_all(self):
        return self.db.query(PipelinesModel).all()

    def get_by_id(self,pipe_id: int):
        return self.db.query(PipelinesModel).filter(PipelinesModel.id == pipe_id).first()

    def update_pipeline(self,pipe_id: int,body:PipelineUpdate):
        pipeline = self.db.query(PipelinesModel).filter(PipelinesModel.id == pipe_id).first()

        if pipeline is None:
            return None

        pipeline.name = body.name
        pipeline.description = body.description
        pipeline.status = body.status

        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline

    def delete_pipeline(self,pipe_id: int):
        pipeline = self.db.query(PipelinesModel).filter(PipelinesModel.id == pipe_id).first()

        if pipeline is None:
            return None

        self.db.delete(pipeline)
        self.db.commit()
        return pipeline