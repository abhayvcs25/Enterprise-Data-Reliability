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

        #ingestion of the csv file
        ingestor = CsvIngestion(file_path=self.file_path)
        ingestion_result = ingestor.ingest()


        quality_result=[]


        #schema validation
        validator = DataValidator()
        expected_schema = {
            "first_name": "str",
            "last_name": "str",
            "location": "str",
            "salary": "int64"
        }
        schema_validation = validator.check_schema(ingestion_result.dataframe, expected_schema)
        quality_result.append(schema_validation)
        

        #null check
        null_validation = validator.check_missing_values(ingestion_result.dataframe)
        quality_result.append(null_validation)

        #duplicate check
        duplicate_validation = validator.check_duplicates(ingestion_result.dataframe)
        quality_result.append(duplicate_validation)

        #range check like min/max value of a given column within a dataframe
        range_validation = validator.check_range(data=ingestion_result.dataframe,column="salary",min_value=1000,max_value=1800000)
        quality_result.append(range_validation)

        #rows check like min/max rows with in a dataframe
        rows_validation = validator.count_rows(data=ingestion_result.dataframe,min_rows=10,max_rows=100)
        quality_result.append(rows_validation)

        #calculation of the results
        total_checks = len(quality_result)

        passed_checks = sum(1 for result in quality_result
                            if result.passed)

        failed_checks = total_checks-passed_checks

        if total_checks > 0:
            quality_score = (passed_checks / total_checks) * 100
        else:
            quality_score = 0

        if schema_validation.passed and rows_validation.passed and range_validation.passed and total_checks > 0:
            overall_status = "PASS"
        else:
            overall_status = "FAIL"

        #getting the metrics of the null and dup
        metrix = {null_validation.name : null_validation.metric,
                duplicate_validation.name : duplicate_validation.message,
                schema_validation.name:schema_validation.metric,
                rows_validation.name : rows_validation.metric,
                range_validation.name:range_validation.metric
                }

        #modifing the dataframe
        transform = DataTransformation()
        transformed_data = transform.transform(ingestion_result.dataframe)

        #storing the transformed dataframe
        parquet_storage = ParquetStorage()
        output_path = f"d:/data/processed/pipeline_{self.pipe_id}/run_{self.run_id}.parquet"
        parquet_storage.save(transformed_data, output_path)
        
        return IngestionResponse(
            metric=metrix,

            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,

            quality_score=quality_score,
            overall_status=overall_status,

            output_path=output_path
        )
