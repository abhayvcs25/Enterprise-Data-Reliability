from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.dataSource_repo import DataSourceRepo
from app.repositories.pipe_data_repo import PipeDataRepo

from app.ingestion.csv_ingestion import CsvIngestion
from app.ingestion.transformations import DataTransformation
from app.ingestion.validation import DataValidator

from app.storage.parquet_storage import ParquetStorage

from app.models.pipelines import PipelineStatus
from app.models.data_source import DataSourceType

from app.quality.quality_result import QualityCheckResult

from fastapi import HTTPException,status
from datetime import datetime



class PipelineExecutionService:
    def __init__(self,pipe_repo:PipelineRepository,pipe_run_repo:PipelineRunRepositroy,datasource_repo:DataSourceRepo,pipe_data_repo:PipeDataRepo):
        self.pipe_repo = pipe_repo
        self.pipe_run_repo = pipe_run_repo
        self.datasource_repo = datasource_repo
        self.pipe_data_repo = pipe_data_repo


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
        pipeline_final_status = PipelineStatus.FAILED
        error_summary = "Unknown execution error"
        
        # Placeholders to prevent local scoping variable errors
        output_data = {}

        try:
            pipe_data = self.pipe_data_repo.get_by_Pipe_id(pipe_id=pipe_id)
            data_source = self.datasource_repo.get_by_id(pipe_data.datasource_id)
        
            if data_source.source_type == DataSourceType.CSV:
                ingestor = CsvIngestion(data_source.location)
                ingestion_result = ingestor.ingest()
                
                validator = DataValidator()
                expected_schema = {
                    "first_name": "str",
                    "last_name": "str",
                    "location": "str",
                    "salary": "int64"
                }
                schema_validation = validator.check_schema(ingestion_result.dataframe, expected_schema)
                if not schema_validation.passed:
                    # Print it to the console as requested earlier                    
                    error_summary = f"Schema validation failed: {schema_validation}"
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={"error": schema_validation.model_dump()}
                    )
                
                range_validation = validator.check_range(data=ingestion_result.dataframe,column="salary",min_value=1000,max_value=1800000)
                if not range_validation.passed:
                    error_summary = f"Range validation failed: {range_validation}"
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={"error": range_validation.model_dump()}
                    )

                rows_validation = validator.count_rows(data=ingestion_result.dataframe,min_rows=10,max_rows=100)
                if not rows_validation.passed:
                    error_summary = f"Range validation failed: {range_validation}"
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={"error": rows_validation.model_dump()}
                    )

                before_missing_values = validator.check_missing_values(ingestion_result.dataframe)
                before_duplicate_rows = validator.check_duplicates(ingestion_result.dataframe)

                before = len(ingestion_result.dataframe)
                transform = DataTransformation()
                transformed_data = transform.transform(ingestion_result.dataframe)
                after = len(transformed_data)
                rows_removed = before - after

                after_missing_values = validator.check_missing_values(transformed_data)
                after_duplicate_rows = validator.check_duplicates(transformed_data)

                parquet_storage = ParquetStorage()
                output_path = f"d:/data/processed/pipeline_{pipeline.id}/run_{run.id}.parquet"
                parquet_storage.save(transformed_data, output_path)
                
                # Map values out for return statement
                output_data = {
                    "row_count": ingestion_result.row_count,
                    "column_name": ingestion_result.column_name,
                    "dtypes": ingestion_result.dtypes,
                    "missing_values": before_missing_values.metric,
                    "duplicate_rows": before_duplicate_rows.metric,
                    "rows_before_transformation": before,
                    "rows_after_transformation": after,
                    "rows_removed": rows_removed,
                    "missing_values_after": after_missing_values.metric,
                    "duplicate_rows_after": after_duplicate_rows.metric,
                    "output_path": output_path
                }
            
            # If execution reaches this point cleanly, flip trackers to SUCCESS
            pipeline_final_status = PipelineStatus.SUCCESS
            error_summary = None
            print(f"Pipeline {pipeline.id} executed successfully")
            return output_data

        except HTTPException as htx:
            # If it's a validation HTTPException, extract detail string/dict for the DB logs
            error_summary = str(htx.detail)
            raise htx
            
        except Exception as e:
            error_summary = f"Internal ingestion crash: {str(e)}"
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
    