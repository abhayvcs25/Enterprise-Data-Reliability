from sqlalchemy.orm import Session
from app.models.data_quality_result import DataQualityResultModel
from app.quality.quality_result import QualityCheckResult

class DataQualityResultRepo:
    def __init__(self,db:Session):
        self.db=db

    def create_many_result(self,quality_results:list,pipeline_run_id:int)->list[DataQualityResultModel]:
        db_results = []

        for result in quality_results:
            db_result = DataQualityResultModel(
                pipeline_run_id=pipeline_run_id,
                check_name=result.check_name,
                passed=result.passed,
                metric=result.metric,
                rows_affected=result.rows_affected,
                message=result.message
            )
            db_results.append(db_result)
        self.db.add_all(db_results)
        self.db.commit()

        for db_result in db_results:
            self.db.refresh(db_result)

        return db_results

    
    def get_by_pipeline_run(self,pipeline_run_id: int) -> list[DataQualityResultModel]:
        return (self.db.query(DataQualityResultModel)
            .filter(DataQualityResultModel.pipeline_run_id == pipeline_run_id).all()
        )