from pydantic import BaseModel
from typing import Any
from datetime import datetime

class DataQualityResultsResponse(BaseModel):
    id :int
    pipeline_run_id :int
    check_name :str
    passed :bool
    metric :Any | None
    rows_affected :int |None
    message : str | None
    created_at:datetime