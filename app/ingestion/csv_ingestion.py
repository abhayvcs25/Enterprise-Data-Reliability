import pandas as pd
import os
from app.quality.ingestion_result import IngestionResults

class CsvIngestion:
    def __init__(self,file_path:str):
        self.file_path = file_path

    def ingest(self):
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"CSV file not found : {self.file_path}")
        
        try:
            data_csv=pd.read_csv(self.file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read the file : {self.file_path}") from e

        data=pd.DataFrame(data_csv)

        preview = data.head().to_dict(orient="records")

        preview = [
            {
                key: value.item() if hasattr(value, "item") else value
                for key, value in row.items()
            }
            for row in preview
        ]

        return IngestionResults(
            dataframe=data,
            row_count= int(len(data)),
            column_name= data.columns.to_list(),
            head= preview,
            dtypes= data.dtypes.astype(str).to_dict()
        )