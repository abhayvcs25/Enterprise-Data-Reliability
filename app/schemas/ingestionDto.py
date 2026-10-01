from pydantic import BaseModel
from typing import Any

class IngestionResponse(BaseModel):
    row_count: int
    column_name: list[str]
    dtypes: dict[str, str]
    schema_validation: dict[str, Any]  
    rows_before_transformation:int
    rows_after_transformation:int
    rows_removed:int
    missing_values:dict[str,int]
    duplicate_rows:int
    missing_values_after:dict[str,int]
    duplicate_rows_after:int
    output_path:str