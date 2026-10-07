from pydantic import BaseModel
from typing import Any

class IngestionResponse(BaseModel):
    pipe_run_id:int
    metric: Any = None

    total_checks: int
    passed_checks: int
    failed_checks: int

    quality_score: float
    overall_status: str

    output_path: str


class IngestionErrorResponse(BaseModel):
    schema_validation: dict[str, Any]