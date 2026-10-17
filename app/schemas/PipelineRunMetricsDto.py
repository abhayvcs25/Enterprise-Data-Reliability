from datetime import datetime

from pydantic import BaseModel

from app.models.pipelines import PipelineStatus


class PipelineRunMetricsResponse(BaseModel):
    pipeline_id: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    pending_runs: int
    running_runs: int
    cancelled_runs: int
    terminal_runs: int
    success_rate: float
    failure_rate: float
    average_duration_seconds: float | None
    latest_run_status: PipelineStatus | None
    latest_run_started_at: datetime | None
    latest_run_finished_at: datetime | None
    latest_successful_run_at: datetime | None
