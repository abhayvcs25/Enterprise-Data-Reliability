import logging
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session
from app.models.pipelinerun import PipelineRunModel
from app.models.pipelines import PipelineStatus


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

    def get_runs_by_pipeline(
        self,
        pipeline_id: int,
        limit: int = 50,
        offset: int = 0,
    ):
        return (
            self.db.query(PipelineRunModel)
            .filter(PipelineRunModel.pipeline_id == pipeline_id)
            .order_by(
                PipelineRunModel.started_at.desc(),
                PipelineRunModel.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_run_by_id(self,run_id:int):
        return (self.db.query(PipelineRunModel).filter(PipelineRunModel.id == run_id).first())

    def update_run(self,run:PipelineRunModel):
        self.db.commit()
        self.db.refresh(run)

        return run

    def get_all_runs(self):
        return self.db.query(PipelineRunModel).all()

    def get_execution_metrics(self, pipeline_id: int) -> dict:
        completed_success = and_(
            PipelineRunModel.status == PipelineStatus.SUCCESS,
            PipelineRunModel.finished_at.isnot(None),
        )
        completed_failure = and_(
            PipelineRunModel.status == PipelineStatus.FAILED,
            PipelineRunModel.finished_at.isnot(None),
        )
        valid_duration = and_(
            PipelineRunModel.status.in_(
                (PipelineStatus.SUCCESS, PipelineStatus.FAILED)
            ),
            PipelineRunModel.started_at.isnot(None),
            PipelineRunModel.finished_at.isnot(None),
            PipelineRunModel.finished_at >= PipelineRunModel.started_at,
        )
        duration_seconds = func.extract(
            "epoch",
            PipelineRunModel.finished_at - PipelineRunModel.started_at,
        )

        aggregate = (
            self.db.query(
                func.count(PipelineRunModel.id).label("total_runs"),
                func.count(
                    case(
                        (PipelineRunModel.status == PipelineStatus.SUCCESS, 1)
                    )
                ).label("successful_runs"),
                func.count(
                    case(
                        (PipelineRunModel.status == PipelineStatus.FAILED, 1)
                    )
                ).label("failed_runs"),
                func.count(
                    case(
                        (PipelineRunModel.status == PipelineStatus.PENDING, 1)
                    )
                ).label("pending_runs"),
                func.count(
                    case(
                        (PipelineRunModel.status == PipelineStatus.RUNNING, 1)
                    )
                ).label("running_runs"),
                func.count(
                    case(
                        (PipelineRunModel.status == PipelineStatus.CANCELLED, 1)
                    )
                ).label("cancelled_runs"),
                func.count(case((completed_success, 1))).label(
                    "completed_successful_runs"
                ),
                func.count(case((completed_failure, 1))).label(
                    "completed_failed_runs"
                ),
                func.avg(
                    case((valid_duration, duration_seconds), else_=None)
                ).label("average_duration_seconds"),
            )
            .filter(PipelineRunModel.pipeline_id == pipeline_id)
            .one()
        )

        latest_run = (
            self.db.query(
                PipelineRunModel.status,
                PipelineRunModel.started_at,
                PipelineRunModel.finished_at,
            )
            .filter(PipelineRunModel.pipeline_id == pipeline_id)
            .order_by(
                func.coalesce(
                    PipelineRunModel.started_at,
                    PipelineRunModel.finished_at,
                ).desc().nullslast(),
                PipelineRunModel.id.desc(),
            )
            .first()
        )

        latest_successful_run_at = (
            self.db.query(PipelineRunModel.finished_at)
            .filter(
                PipelineRunModel.pipeline_id == pipeline_id,
                PipelineRunModel.status == PipelineStatus.SUCCESS,
                PipelineRunModel.finished_at.isnot(None),
            )
            .order_by(
                PipelineRunModel.finished_at.desc(),
                PipelineRunModel.id.desc(),
            )
            .limit(1)
            .scalar()
        )

        return {
            "total_runs": aggregate.total_runs,
            "successful_runs": aggregate.successful_runs,
            "failed_runs": aggregate.failed_runs,
            "pending_runs": aggregate.pending_runs,
            "running_runs": aggregate.running_runs,
            "cancelled_runs": aggregate.cancelled_runs,
            "completed_successful_runs": aggregate.completed_successful_runs,
            "completed_failed_runs": aggregate.completed_failed_runs,
            "average_duration_seconds": aggregate.average_duration_seconds,
            "latest_run_status": latest_run.status if latest_run else None,
            "latest_run_started_at": latest_run.started_at if latest_run else None,
            "latest_run_finished_at": latest_run.finished_at if latest_run else None,
            "latest_successful_run_at": latest_successful_run_at,
        }

    
