import logging
from sqlalchemy.orm import Session
from app.models.pipelinerun import PipelineRunModel
from app.schemas.PipelinesDto import PipelineStatus


logger = logging.getLogger(__name__)


class PipelineRunRepositroy:
    def __init__(self,db : Session):
        self.db = db

    def create_run(self,pipeline_id:int,status:PipelineStatus):
        run = PipelineRunModel(
            pipeline_id = pipeline_id,
            status = status
        )

        self.db.add(run)
        try:
            self.db.flush()
            self.db.refresh(run)
            self.db.commit()
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                logger.exception(
                    "Rollback failed after pipeline run creation failed "
                    "for pipeline_id=%s",
                    pipeline_id,
                )
            raise

        return run

    def get_runs_by_pipeline(self,pipeline_id:int):
        return (self.db.query(PipelineRunModel).filter(PipelineRunModel.pipeline_id == pipeline_id).all())

    def get_run_by_id(self,run_id:int):
        return (self.db.query(PipelineRunModel).filter(PipelineRunModel.id == run_id).first())

    def update_run(self,run:PipelineRunModel):
        self.db.commit()
        self.db.refresh(run)

        return run

    def get_all_runs(self):
        return self.db.query(PipelineRunModel).all()

    
