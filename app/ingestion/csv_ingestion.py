import pandas as pd
import os

class CsvIngestion:
    def __init__(self,file_path:str):
        self.file_path = file_path

    def ingest(self):
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"CSV file not found : {self.file_path}")
        
        try:
            data_csv=pd.read_csv(self.file_path)
        except Exception as e:
            raise CsvIngestion(f"Failed to read the file : {self.file_path}") from e

        data=pd.DataFrame(data_csv)

        return {
            "success":True,
            "file_path": self.file_path,
            "rows":int(len(data)),
            "columns": int(len(data.columns)),
            "columns_name":list(data.columns),
            "dataframe": data.head().to_dict(orient="records")
        }