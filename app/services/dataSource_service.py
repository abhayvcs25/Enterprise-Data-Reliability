from fastapi import HTTPException
from app.repositories.dataSource_repo import DataSourceRepo
from app.schemas.datasourceDto import DataSourceUpdate,DataSourceCreate
from app.ingestion.csv_ingestion import CsvIngestion
from app.models.data_source import DataSourceType


class DataSourceServices:
    def __init__(self,data_repo:DataSourceRepo):
        self.data_repo = data_repo

    def create_data_source(self,data:DataSourceCreate):
        return self.data_repo.create_dataSource(data)

    def get_all_data_source(self):
        return self.data_repo.get_all()

    def get_data_source_by_id(self,data_s_id:int):
        data = self.data_repo.get_by_id(data_s_id)

        if data is None:
            raise HTTPException(status_code=404,detail="data source id not found")

        return data

    def update_data_source(self,data_s_id:int,update_data:DataSourceUpdate):
        data_source = self.data_repo.get_by_id(data_s_id)

        if data_source is None:
            raise HTTPException(status_code=404,detail="data source id not found")

        return self.data_repo.update(data_source,update_data)

    def delete_data_source(self,data_s_id:int):
        data_source = self.data_repo.get_by_id(data_s_id)

        if data_source is None:
            raise HTTPException(status_code=404,detail="data source id not found")

        self.data_repo.delete(data_source)

        return {
            "message":"DataSource deleted successfully"
        }

    def ingest_data_s(self,data_s_id:int):

        data_source = self.data_repo.get_by_id(data_s_id)

        if data_source is None:
            raise HTTPException(status_code=404,detail="data source id not found")

        if DataSourceType.CSV == data_source.source_type:
            ingestor = CsvIngestion(data_source.location)
            return ingestor.ingest()

        raise HTTPException(status_code=400,detail=f"Unsupported datasource type: {data_source.source_type}")