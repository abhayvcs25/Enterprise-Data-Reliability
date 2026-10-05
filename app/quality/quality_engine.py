from app.ingestion.csv_ingestion import CsvIngestion
from app.ingestion.transformations import DataTransformation
from app.ingestion.validation import DataValidator

from fastapi import HTTPException,status

from app.storage.parquet_storage import ParquetStorage

from app.schemas.ingestionDto import IngestionResponse
class QualityEngine:
    def __init__(self,file_path:str,pipe_id:int,run_id:int)->IngestionResponse:
        self.file_path = file_path
        self.pipe_id = pipe_id
        self.run_id = run_id

    def CsvQualityEngine(self):
        ingestor = CsvIngestion(file_path=self.file_path)
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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_summary":f"Schema validation failed: {schema_validation.model_dump()}"}
            )
        
        range_validation = validator.check_range(data=ingestion_result.dataframe,column="salary",min_value=1000,max_value=1800000)
        if not range_validation.passed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_summary": f"Range validation failed: {range_validation.model_dump()}"}
            )

        rows_validation = validator.count_rows(data=ingestion_result.dataframe,min_rows=10,max_rows=100)
        if not rows_validation.passed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_summary": f"Range validation failed: {rows_validation.model_dump()}"}
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
        output_path = f"d:/data/processed/pipeline_{self.pipe_id}/run_{self.run_id}.parquet"
        parquet_storage.save(transformed_data, output_path)
        
        # Map values out for return statement
        return IngestionResponse(
            row_count= ingestion_result.row_count,
            column_name= ingestion_result.column_name,
            dtypes=ingestion_result.dtypes,
            missing_values=before_missing_values.metric,
            duplicate_rows=before_duplicate_rows.metric,
            rows_before_transformation=before,
            rows_after_transformation= after,
            rows_removed= rows_removed,
            missing_values_after= after_missing_values.metric,
            duplicate_rows_after= after_duplicate_rows.metric,
            output_path= output_path
        )
