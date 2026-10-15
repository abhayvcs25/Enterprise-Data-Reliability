from app.ingestion.csv_ingestion import CsvIngestion
from app.ingestion.transformations import DataTransformation
from app.ingestion.validation import DataValidator

from app.repositories.data_quality_result_repository import DataQualityResultRepo

from app.services.dataqualityresult import DataQualityResultService

from app.storage.parquet_storage import ParquetStorage

from app.schemas.ingestionDto import IngestionResponse

class QualityEngine:
    def __init__(self,file_path:str,pipe_id:int,run_id:int,data_quality_repo:DataQualityResultRepo,configuration: dict | None = None)->IngestionResponse:
        self.file_path = file_path
        self.pipe_id = pipe_id
        self.run_id = run_id
        self.data_quality_repo=data_quality_repo
        self.configuration =configuration or {} 

    def _get_data_quality_rules(self) -> dict:
        data_quality = self.configuration.get("data_quality")

        if data_quality is None:
            return {}

        if not data_quality.get("enabled", False):
            return {}

        return data_quality.get("rules", {})

    def CsvQualityEngine(self):

        #ingestion of the csv file
        ingestor = CsvIngestion(file_path=self.file_path)
        ingestion_result = ingestor.ingest()


        quality_result=[]


        #schema validation
        rules = self._get_data_quality_rules()

        quality_result = []

        validator = DataValidator()

        schema_validation = None
        null_validation = None
        duplicate_validation = None
        range_validation = None
        rows_validation = None


        # -------------------------
        # Schema check
        # -------------------------

        schema_config = rules.get("schema")

        if schema_config and schema_config.get("enabled", False):
            expected_schema = schema_config.get("columns", {})

            schema_validation = validator.check_schema(
                ingestion_result.dataframe,
                expected_schema
            )

            quality_result.append(schema_validation)


        # -------------------------
        # Null check
        # -------------------------

        null_config = rules.get("null_check")

        if null_config and null_config.get("enabled", False):

            null_validation = validator.check_missing_values(
                ingestion_result.dataframe
            )

            quality_result.append(null_validation)


        # -------------------------
        # Duplicate check
        # -------------------------

        duplicate_config = rules.get("duplicate_check")

        if duplicate_config and duplicate_config.get("enabled", False):

            duplicate_validation = validator.check_duplicates(
                ingestion_result.dataframe
            )

            quality_result.append(duplicate_validation)


        # -------------------------
        # Range check
        # -------------------------

        range_config = rules.get("range_check")

        if range_config and range_config.get("enabled", False):

            range_columns = range_config.get("columns", {})

            for column, config in range_columns.items():

                range_validation = validator.check_range(
                    data=ingestion_result.dataframe,
                    column=column,
                    min_value=config.get("min"),
                    max_value=config.get("max"),
                    min_inclusive=config.get("min_inclusive", True),
                    max_inclusive=config.get("max_inclusive", True)
                )

                quality_result.append(range_validation)


        # -------------------------
        # Row count check
        # -------------------------

        row_count_config = rules.get("row_count")

        if row_count_config and row_count_config.get("enabled", False):

            rows_validation = validator.count_rows(
                data=ingestion_result.dataframe,
                min_rows=row_count_config.get("min"),
                max_rows=row_count_config.get("max")
            )

            quality_result.append(rows_validation)


        #calculation of the results
        total_checks = len(quality_result)

        passed_checks = sum(
            1 for result in quality_result
            if result.passed
        )

        failed_checks = total_checks - passed_checks

        if total_checks > 0:
            quality_score = (passed_checks / total_checks) * 100
        else:
            quality_score = 100

        overall_status = (
            "PASS"
            if total_checks > 0 and failed_checks == 0
            else "FAIL"
        )

        #getting the metrics of the null and dup
        metrix={
            result.check_name: result.metric
            for result in quality_result
        }
        #modifing the dataframe
        transform = DataTransformation()
        transformed_data = transform.transform(ingestion_result.dataframe)

        #storing the transformed dataframe
        parquet_storage = ParquetStorage()
        output_path = f"d:/data/processed/pipeline_{self.pipe_id}/run_{self.run_id}.parquet"
        parquet_storage.save(transformed_data, output_path)

        data_quality_service = DataQualityResultService(data_quality_repo=self.data_quality_repo)
        results = data_quality_service.create_many(quality_result,pipe_run_id=self.run_id)
        if results is not None:
            print("++data quality results inserted successfuly")
    
        
        return IngestionResponse(
            pipe_run_id = self.run_id,
            metric=metrix,

            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,

            quality_score=quality_score,
            overall_status=overall_status,

            output_path=output_path
        )
