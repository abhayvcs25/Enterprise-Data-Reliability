from app.repositories.data_quality_result_repository import DataQualityResultRepo

class DataQualityResultService:
    def __init__(self,data_quality_repo:DataQualityResultRepo):
        self.data_quality_repo=data_quality_repo
        
    def create_many(self,quality_results:list,pipe_run_id:int):
        return self.data_quality_repo.create_many_result(
            quality_results=quality_results,
            pipeline_run_id=pipe_run_id            
        )
