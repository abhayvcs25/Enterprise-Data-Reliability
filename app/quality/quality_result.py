from pydantic import BaseModel
from typing import Any

#this is used in the validator.py file
class QualityCheckResult(BaseModel):
    name:str
    passed:bool
    rows_affected :int | None = None
    metric: Any = None
    message:str
