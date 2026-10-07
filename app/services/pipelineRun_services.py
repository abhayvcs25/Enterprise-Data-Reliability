from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.dataSource_repo import DataSourceRepo
from app.repositories.pipe_data_repo import PipeDataRepo
from app.repositories.data_quality_result_repository import DataQualityResultRepo

from app.models.pipelines import PipelineStatus
from app.models.data_source import DataSourceType

from app.quality.quality_engine import QualityEngine

from fastapi import HTTPException,status
from datetime import datetime



class PipelineExecutionService:
    def __init__(self,pipe_repo:PipelineRepository,pipe_run_repo:PipelineRunRepositroy,datasource_repo:DataSourceRepo,pipe_data_repo:PipeDataRepo,data_quality_repo:DataQualityResultRepo):
        self.pipe_repo = pipe_repo
        self.pipe_run_repo = pipe_run_repo
        self.datasource_repo = datasource_repo
        self.pipe_data_repo = pipe_data_repo
        self.data_quality_repo=data_quality_repo


    def run_pipeline(self, pipe_id: int):
        # 1. Pipeline verification
        pipeline = self.pipe_repo.get_by_id(pipe_id)
        if pipeline is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pipeline id not found")

        if pipeline.status == PipelineStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline is already running"
            )

        # 2. Initialize the run tracker
        run = self.pipe_run_repo.create_run(pipeline_id=pipeline.id, status=PipelineStatus.PENDING)
        
        # Ensure run.started_at is set (if your repo doesn't do it, set it here: run.started_at = datetime.now())
        run.status = PipelineStatus.RUNNING
        self.pipe_run_repo.update_run(run)
        self.pipe_repo.update_pipeline_status(pipeline.id, PipelineStatus.RUNNING)
        
        # Trackers for the final state
        
        error_summary = "Unknown execution error"
        

        try:
            pipe_data = self.pipe_data_repo.get_by_Pipe_id(pipe_id=pipe_id)
            data_source = self.datasource_repo.get_by_id(pipe_data.datasource_id)

            engine = QualityEngine(file_path=data_source.location,pipe_id=pipeline.id,run_id=run.id,data_quality_repo=self.data_quality_repo)
        
            if data_source.source_type == DataSourceType.CSV:
                try:
                    output_data = engine.CsvQualityEngine()
                except Exception as e:
                    pipeline_final_status = PipelineStatus.FAILED
                    raise e

            if output_data.overall_status == "PASS":
                pipeline_final_status = PipelineStatus.SUCCESS
                error_summary = None
                print(f"++Pipeline {pipeline.id} executed successfully")
            else:
                print(f"++Pipeline {pipeline.id} executed failed")
                pipeline_final_status = PipelineStatus.FAILED
                error_summary = f"there where {output_data.failed_checks} checks failed and the score was {output_data.quality_score}"
                raise HTTPException(
                                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                                detail=output_data.model_dump()
                            )
            
            return output_data

        except HTTPException as htx:
            raise htx
            
        except Exception as e:
            error_summary = f"Internal ingestion crash: {str(e)}"
            print(f"++Pipeline {pipeline.id} executed failed because of a execption :: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_summary
            )
            
        finally:
            # 🛑 THIS ALWAYS RUNS SAFELY FOR SUCCESS & FAILURE 🛑
            try:
                finished_at = datetime.now()
                run.status = pipeline_final_status
                run.finished_at = finished_at
                
                # Calculate duration safely assuming run.started_at exists
                if hasattr(run, 'started_at') and run.started_at:
                    run.duration = (finished_at - run.started_at).total_seconds()
                
                run.error_message = error_summary
                
                # Save the true status (SUCCESS or FAILED) to the DB
                self.pipe_run_repo.update_run(run)
                self.pipe_repo.update_pipeline_status(pipeline.id, pipeline_final_status)
            except Exception as db_err:
                print(f"Critial Failure writing final status metrics to DB: {db_err}")


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
    