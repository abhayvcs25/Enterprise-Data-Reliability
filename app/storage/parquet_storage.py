import os
import pandas as pd


class ParquetStorage:

    def save(self, data: pd.DataFrame, file_path: str) -> str:

        directory = os.path.dirname(file_path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        data.to_parquet(file_path, index=False)

        return file_path


