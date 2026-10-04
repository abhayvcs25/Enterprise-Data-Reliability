from pandas import DataFrame
from dataclasses import dataclass

@dataclass
class IngestionResults:
    dataframe : DataFrame
    row_count: int
    column_name : list[str]
    head: list[dict]
    dtypes: dict[str,str]