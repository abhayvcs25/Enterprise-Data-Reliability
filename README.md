# Enterprise Data Reliability & DataOps Platform

This repository currently provides a FastAPI service for managing pipelines and
executing CSV-based pipeline runs.

## Pipeline execution and run tracking

- `POST /api/v1/pipelines/{pipeline_id}/run` starts a run and records its
  `PENDING`, `RUNNING`, and terminal status in `Pipeline_Runs`.
- Run records reference their pipeline and include start, finish, duration, and
  a sanitized error summary. Run-read API responses omit the stored error
  summary.
- Configured Data Quality checks run before transformation and storage.
  Failed checks are persisted against the run that produced them and prevent
  transformation/storage; execution failures and quality violations both
  result in a failed run, while persisted check outcomes distinguish quality
  violations.
- Successful execution transforms the CSV data and writes Parquet output using
  the existing storage component.

## Run history and metrics

- `GET /api/v1/pipelines/{pipeline_id}/runs` returns newest-first run history;
  `limit` defaults to 50 (maximum 100) and `offset` defaults to 0.
- `GET /api/v1/pipelines/{pipeline_id}/runs/{run_id}` returns a run only when it
  belongs to the requested pipeline.
- `GET /api/v1/pipelines/{pipeline_id}/metrics` returns status counts,
  completed success/failure rates, average valid completed-run duration, and
  the most recent run and successful completion timestamps.
- `GET /api/v1/pipeline-run-DQR/{pipe_run_id}` returns persisted quality-check
  results for one run.

The run-history, individual-run, and metrics endpoints return HTTP 404 for a
pipeline that does not exist. History pagination is validated, and history and
individual-run lookups are scoped to the requested pipeline.
