from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.dataSource_repo import DataSourceRepo
from app.repositories.pipe_data_repo import PipeDataRepo

from app.ingestion.csv_ingestion import CsvIngestion
from app.services.dataSource_service import DataSourceServices

from app.models.pipelines import PipelineStatus
from app.models.data_source import DataSourceType

from fastapi import HTTPException
from datetime import datetime

class PipelineExecutionService:
    def __init__(self,pipe_repo:PipelineRepository,pipe_run_repo:PipelineRunRepositroy,datasource_repo:DataSourceRepo,pipe_data_repo:PipeDataRepo):
        self.pipe_repo = pipe_repo
        self.pipe_run_repo = pipe_run_repo
        self.datasource_repo = datasource_repo
        self.pipe_data_repo = pipe_data_repo

    def run_pipeline(self,pipe_id:int):

        pipeline = self.pipe_repo.get_by_id(pipe_id)
        if pipeline is None:
            raise HTTPException(status_code=404,detail="pipeline id not found")

        if pipeline.status == PipelineStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail="Pipeline is already running"
            )

        run = self.pipe_run_repo.create_run(pipeline_id = pipeline.id,status = PipelineStatus.PENDING)

        run.status = PipelineStatus.RUNNING
        self.pipe_run_repo.update_run(run)

        self.pipe_repo.update_pipeline_status(pipeline.id,PipelineStatus.RUNNING)
        
        try:
            pipe_data = self.pipe_data_repo.get_by_Pipe_id(pipe_id=pipe_id)
            
            data_source = self.datasource_repo.get_by_id(pipe_data.datasource_id)
                        
            if DataSourceType.CSV == data_source.source_type:
                ingestor = CsvIngestion(data_source.location)
                transformed_data = ingestor.ingest()
            
            finished_at = datetime.now()
            run.status= PipelineStatus.SUCCESS
            run.finished_at = finished_at
            run.duration = (finished_at - run.started_at).total_seconds()
            run.error_message = None
            self.pipe_run_repo.update_run(run)

            self.pipe_repo.update_pipeline_status(pipeline.id,PipelineStatus.SUCCESS)

            print(f"Pipeline {pipeline.id} executed successfully")
            return transformed_data
        except HTTPException as htx:
            raise htx
        except Exception as e:
            finished_at = datetime.now()
            
            run.status= PipelineStatus.FAILED
            run.finished_at = finished_at
            run.finished_at = (finished_at - run.started_at).total_seconds()
            run.error_message = str(e)
            self.pipe_run_repo.update_run(run)

            self.pipe_repo.update_pipeline_status(pipeline.id,PipelineStatus.FAILED)

            raise HTTPException(status_code=500,detail=f"Internal ingestion crash:{str(e)}")

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
    