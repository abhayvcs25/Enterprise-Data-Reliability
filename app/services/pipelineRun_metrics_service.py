from app.repositories.pipelineRun_repo import PipelineRunRepositroy


class PipelineRunMetricsService:
    """Calculate success/failure rates over completed runs and mean valid duration.

    Rates use completed successes plus completed failures as the denominator;
    average duration uses only completed runs with valid start/finish timestamps.
    """

    def __init__(self, pipeline_run_repo: PipelineRunRepositroy):
        self.pipeline_run_repo = pipeline_run_repo

    def get_pipeline_metrics(self, pipeline_id: int) -> dict:
        run_metrics = self.pipeline_run_repo.get_execution_metrics(pipeline_id)
        completed_successful = run_metrics["completed_successful_runs"]
        completed_failed = run_metrics["completed_failed_runs"]
        terminal_runs = completed_successful + completed_failed

        if terminal_runs:
            success_rate = completed_successful / terminal_runs * 100
            failure_rate = completed_failed / terminal_runs * 100
        else:
            success_rate = 0.0
            failure_rate = 0.0

        average_duration = run_metrics["average_duration_seconds"]

        return {
            "pipeline_id": pipeline_id,
            "total_runs": run_metrics["total_runs"],
            "successful_runs": run_metrics["successful_runs"],
            "failed_runs": run_metrics["failed_runs"],
            "pending_runs": run_metrics["pending_runs"],
            "running_runs": run_metrics["running_runs"],
            "cancelled_runs": run_metrics["cancelled_runs"],
            "terminal_runs": terminal_runs,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_duration_seconds": (
                float(average_duration) if average_duration is not None else None
            ),
            "latest_run_status": run_metrics["latest_run_status"],
            "latest_run_started_at": run_metrics["latest_run_started_at"],
            "latest_run_finished_at": run_metrics["latest_run_finished_at"],
            "latest_successful_run_at": run_metrics["latest_successful_run_at"],
        }
