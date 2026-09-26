from sqlalchemy.orm import Session
from app.models.pipelines import PipelinesModel
from app.schemas.PipelinesDto import PipelineCreate



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