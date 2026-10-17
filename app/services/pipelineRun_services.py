import logging
from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.dataSource_repo import DataSourceRepo
from app.repositories.pipe_data_repo import PipeDataRepo
from app.repositories.data_quality_result_repository import DataQualityResultRepo

from app.models.pipelines import PipelineStatus
from app.models.data_source import DataSourceType

from app.ingestion.csv_ingestion import CsvInputError
from app.quality.quality_engine import QualityEngine

from fastapi import HTTPException,status
from datetime import datetime


logger = logging.getLogger(__name__)


class PipelineExecutionService:
    def __init__(self,pipe_repo:PipelineRepository,pipe_run_repo:PipelineRunRepositroy,datasource_repo:DataSourceRepo,pipe_data_repo:PipeDataRepo,data_quality_repo:DataQualityResultRepo):
        self.pipe_repo = pipe_repo
        self.pipe_run_repo = pipe_run_repo
        self.datasource_repo = datasource_repo
        self.pipe_data_repo = pipe_data_repo
        self.data_quality_repo=data_quality_repo

    def _rollback_session(self, pipeline_id: int, run_id: int | None, context: str):
        try:
            self.pipe_run_repo.db.rollback()
        except Exception:
            logger.exception(
                "Database rollback failed during %s for pipeline_id=%s run_id=%s",
                context,
                pipeline_id,
                run_id,
            )

    def run_pipeline(self, pipe_id: int):
        # 1. Pipeline verification
        try:
            pipeline = self.pipe_repo.get_by_id(pipe_id)
        except Exception as e:
            self._rollback_session(pipe_id, None, "pipeline lookup")
            logger.exception("Could not load pipeline pipeline_id=%s", pipe_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline could not be loaded."
            ) from e

        if pipeline is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pipeline id not found")

        if pipeline.status == PipelineStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline is already running"
            )

        # 2. Initialize the run tracker
        try:
            run = self.pipe_run_repo.create_run(
                pipeline_id=pipeline.id,
                status=PipelineStatus.PENDING
            )
        except Exception as e:
            self._rollback_session(pipeline.id, None, "run creation")
            logger.exception(
                "Could not create pipeline run for pipeline_id=%s",
                pipeline.id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline run could not be created."
            ) from e

        pipeline_final_status = PipelineStatus.FAILED
        error_summary = "Pipeline execution failed."
        execution_error = None
        output_data = None

        try:
            run.status = PipelineStatus.RUNNING
            self.pipe_run_repo.update_run(run)
            self.pipe_repo.update_pipeline_status(pipeline.id, PipelineStatus.RUNNING)

            pipe_data = self.pipe_data_repo.get_by_Pipe_id(pipe_id=pipe_id)
            if pipe_data is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Pipeline has no configured data source."
                )

            data_source = self.datasource_repo.get_by_id(pipe_data.datasource_id)
            if data_source is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="The configured data source was not found."
                )

            if data_source.source_type != DataSourceType.CSV:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="The configured data source type is not supported."
                )

            # Release the read transaction before ingestion and other long-running work.
            self.pipe_run_repo.db.commit()

            engine = QualityEngine(
                file_path=data_source.location,
                pipe_id=pipeline.id,
                run_id=run.id,
                data_quality_repo=self.data_quality_repo,
                configuration=data_source.configuration
            )
            output_data = engine.CsvQualityEngine()

            if output_data.overall_status == "PASS":
                pipeline_final_status = PipelineStatus.SUCCESS
                error_summary = None
            else:
                pipeline_final_status = PipelineStatus.FAILED
                error_summary = (
                    f"Data Quality checks failed: {output_data.failed_checks} "
                    "check(s) failed."
                )
                logger.warning(
                    "Data Quality checks failed for pipeline_id=%s run_id=%s "
                    "failed_checks=%s",
                    pipeline.id,
                    run.id,
                    output_data.failed_checks,
                )
                execution_error = HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=output_data.model_dump()
                )

        except HTTPException as e:
            pipeline_final_status = PipelineStatus.FAILED
            safe_validation_details = (
                "Pipeline has no configured data source.",
                "The configured data source was not found.",
                "The configured data source type is not supported.",
            )
            if (
                400 <= e.status_code < 500
                and isinstance(e.detail, str)
                and e.detail in safe_validation_details
            ):
                error_summary = e.detail
                execution_error = e
                logger.warning(
                    "Pipeline validation failed for pipeline_id=%s run_id=%s status=%s",
                    pipeline.id,
                    run.id,
                    e.status_code,
                )
            else:
                error_summary = "Pipeline execution failed due to an internal error."
                execution_error = HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Pipeline execution failed."
                )
                logger.error(
                    "Unexpected HTTP error during pipeline_id=%s run_id=%s status=%s",
                    pipeline.id,
                    run.id,
                    e.status_code,
                    exc_info=(type(e), e, e.__traceback__),
                )
            self._rollback_session(pipeline.id, run.id, "validation failure")

        except FileNotFoundError:
            pipeline_final_status = PipelineStatus.FAILED
            error_summary = "CSV input file was not found."
            execution_error = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_summary
            )
            logger.warning(
                "CSV input file was not found for pipeline_id=%s run_id=%s",
                pipeline.id,
                run.id,
            )
            self._rollback_session(pipeline.id, run.id, "missing CSV input")

        except CsvInputError:
            pipeline_final_status = PipelineStatus.FAILED
            error_summary = "CSV input is empty or malformed."
            execution_error = HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_summary
            )
            logger.warning(
                "CSV input validation failed for pipeline_id=%s run_id=%s",
                pipeline.id,
                run.id,
            )
            self._rollback_session(pipeline.id, run.id, "invalid CSV input")

        except Exception:
            pipeline_final_status = PipelineStatus.FAILED
            error_summary = "Pipeline execution failed due to an internal error."
            logger.exception(
                "Pipeline execution failed for pipeline_id=%s run_id=%s",
                pipeline.id,
                run.id,
            )
            execution_error = HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline execution failed."
            )
            self._rollback_session(pipeline.id, run.id, "execution failure")

        try:
            finished_at = datetime.now()
            run.status = pipeline_final_status
            run.finished_at = finished_at

            if hasattr(run, 'started_at') and run.started_at:
                run.duration = (finished_at - run.started_at).total_seconds()

            run.error_message = error_summary

            self.pipe_run_repo.update_run(run)
            self.pipe_repo.update_pipeline_status(pipeline.id, pipeline_final_status)
        except Exception as db_err:
            self._rollback_session(pipeline.id, run.id, "final status persistence")
            logger.exception(
                "Could not persist final status for pipeline_id=%s run_id=%s",
                pipeline.id,
                run.id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline run outcome could not be confirmed."
            ) from db_err

        if execution_error is not None:
            raise execution_error

        return output_data


    def get_run(self,run_id:int):
        run = self.pipe_run_repo.get_run_by_id(run_id)

        if run is None:
            raise HTTPException(status_code=404,detail="run id not found")

        return run

    def get_pipeline_runs(self,pipe_id:int):
        pipeline = self.pipe_repo.get_by_id(pipe_id)

        if pipeline is None:
            raise HTTPException(status_code=404,detail="pipeline id not found")

        return self.pipe_run_repo.get_runs_by_pipeline(pipeline.id)

    def get_all_run(self):
        return self.pipe_run_repo.get_all_runs()
    