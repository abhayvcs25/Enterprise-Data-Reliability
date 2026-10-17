import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.functions import Extract

from app.db.db import Base, get_db
from app.main import app
from app.models.data_quality_result import DataQualityResultModel
from app.models.data_source import DataSourceModel, DataSourceType
from app.models.pipe_dataSource_M_M_relation import PipelineDataSourceModel
from app.models.pipelinerun import PipelineRunModel
from app.models.pipelines import PipelineStatus, PipelinesModel
from app.repositories.pipelineRun_repo import PipelineRunRepositroy
from app.storage.parquet_storage import ParquetStorage


@compiles(Extract, "sqlite")
def _compile_sqlite_extract(element, compiler, **kwargs):
    expression = element.expr
    return (
        "(julianday(%s) - julianday(%s)) * 86400.0"
        % (
            compiler.process(expression.left, **kwargs),
            compiler.process(expression.right, **kwargs),
        )
    )


class Phase8ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(self.engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        app.dependency_overrides[get_db] = self._override_get_db
        self.client = TestClient(app)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        self.temp_dir.cleanup()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _override_get_db(self):
        session = self.Session()
        try:
            yield session
        finally:
            session.close()

    def _session(self):
        return self.Session()

    def _create_pipeline(self, name="test-pipeline"):
        session = self._session()
        try:
            pipeline = PipelinesModel(
                name=name,
                status=PipelineStatus.PENDING,
            )
            session.add(pipeline)
            session.commit()
            session.refresh(pipeline)
            return pipeline.id
        finally:
            session.close()

    def _create_source(self, pipeline_id, file_path, configuration=None):
        session = self._session()
        try:
            data_source = DataSourceModel(
                name=f"source-{pipeline_id}",
                source_type=DataSourceType.CSV,
                location=file_path,
                configuration=configuration,
            )
            session.add(data_source)
            session.flush()
            connection = PipelineDataSourceModel(
                pipeline_id=pipeline_id,
                datasource_id=data_source.id,
                execution_order=1,
            )
            session.add(connection)
            session.commit()
            return data_source.id
        finally:
            session.close()

    def _create_run(self, pipeline_id, status, started_at, finished_at=None):
        session = self._session()
        try:
            run = PipelineRunModel(
                pipeline_id=pipeline_id,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run.id
        finally:
            session.close()

    def _get_run(self, run_id):
        session = self._session()
        try:
            return session.query(PipelineRunModel).filter_by(id=run_id).one()
        finally:
            session.close()

    def _csv(self, content="name,value\nA,1\nB,2\n"):
        path = os.path.join(self.temp_dir.name, f"input-{len(os.listdir(self.temp_dir.name))}.csv")
        with open(path, "w", encoding="utf-8") as csv_file:
            csv_file.write(content)
        return path

    def _execute(self, pipeline_id, storage_patch=None):
        storage_patch = storage_patch or patch(
            "app.quality.quality_engine.ParquetStorage.save",
            return_value="test-output.parquet",
        )
        with storage_patch:
            return self.client.post(
                f"/api/v1/pipelines/{pipeline_id}/run"
            )

    def test_success_lifecycle_persists_transitions_and_pipeline(self):
        pipeline_id = self._create_pipeline()
        self._create_source(pipeline_id, self._csv())
        observed_statuses = []
        original_create = PipelineRunRepositroy.create_run
        original_update = PipelineRunRepositroy.update_run
        original_save = ParquetStorage.save
        stored_output_path = os.path.join(
            self.temp_dir.name, "actual-output.parquet"
        )

        def observe_create(repository, *args, **kwargs):
            run = original_create(repository, *args, **kwargs)
            observed_statuses.append(self._get_run(run.id).status)
            return run

        def observe_update(repository, run):
            result = original_update(repository, run)
            observed_statuses.append(self._get_run(run.id).status)
            return result

        def save_output(data, requested_path):
            self.assertEqual(
                requested_path,
                f"d:/data/processed/pipeline_{pipeline_id}/run_1.parquet",
            )
            return original_save(ParquetStorage(), data, stored_output_path)

        with patch.object(PipelineRunRepositroy, "create_run", observe_create), patch.object(
            PipelineRunRepositroy, "update_run", observe_update
        ), patch(
            "app.quality.quality_engine.ParquetStorage.save",
            side_effect=save_output,
        ):
            response = self.client.post(
                f"/api/v1/pipelines/{pipeline_id}/run"
            )

        self.assertEqual(response.status_code, 200, response.text)
        run_id = response.json()["pipe_run_id"]
        run = self._get_run(run_id)
        self.assertEqual(run.pipeline_id, pipeline_id)
        self.assertEqual(run.status, PipelineStatus.SUCCESS)
        session = self._session()
        try:
            pipeline = session.query(PipelinesModel).filter_by(
                id=pipeline_id
            ).one()
            self.assertEqual(pipeline.status, PipelineStatus.SUCCESS)
        finally:
            session.close()
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.finished_at)
        self.assertGreaterEqual(run.duration, 0)
        self.assertIsNone(run.error_message)
        self.assertEqual(
            observed_statuses,
            [
                PipelineStatus.PENDING,
                PipelineStatus.RUNNING,
                PipelineStatus.SUCCESS,
            ],
        )
        self.assertEqual(
            response.json()["output_path"],
            f"d:/data/processed/pipeline_{pipeline_id}/run_{run_id}.parquet",
        )
        stored_data = pd.read_parquet(stored_output_path)
        self.assertEqual(stored_data.to_dict(orient="records"), [
            {"name": "A", "value": 1},
            {"name": "B", "value": 2},
        ])

    def test_invalid_pipeline_and_missing_or_invalid_source_are_recorded(self):
        missing_pipeline = self.client.post(
            "/api/v1/pipelines/2147483000/run"
        )
        self.assertEqual(missing_pipeline.status_code, 404)

        pipeline_without_source = self._create_pipeline("no-source")
        response = self.client.post(
            f"/api/v1/pipelines/{pipeline_without_source}/run"
        )
        self.assertEqual(response.status_code, 422)

        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=pipeline_without_source
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertIsNotNone(run.finished_at)
            self.assertEqual(run.error_message, "Pipeline has no configured data source.")
        finally:
            session.close()

        unsupported_pipeline = self._create_pipeline("unsupported-source")
        session = self._session()
        try:
            source = DataSourceModel(
                name=f"source-{unsupported_pipeline}",
                source_type=DataSourceType.POSTGRESQL,
                location="not-used",
            )
            session.add(source)
            session.flush()
            session.add(
                PipelineDataSourceModel(
                    pipeline_id=unsupported_pipeline,
                    datasource_id=source.id,
                    execution_order=1,
                )
            )
            session.commit()
        finally:
            session.close()

        response = self.client.post(
            f"/api/v1/pipelines/{unsupported_pipeline}/run"
        )
        self.assertEqual(response.status_code, 422)
        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=unsupported_pipeline
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertEqual(
                run.error_message,
                "The configured data source type is not supported.",
            )
            self.assertIsNotNone(run.finished_at)
        finally:
            session.close()

        missing_file_pipeline = self._create_pipeline("missing-file")
        missing_path = os.path.join(self.temp_dir.name, "absent.csv")
        self._create_source(missing_file_pipeline, missing_path)
        response = self.client.post(
            f"/api/v1/pipelines/{missing_file_pipeline}/run"
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(missing_path, response.text)
        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=missing_file_pipeline
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertEqual(run.error_message, "CSV input file was not found.")
            self.assertIsNotNone(run.finished_at)
        finally:
            session.close()

        malformed_pipeline = self._create_pipeline("malformed-csv")
        self._create_source(malformed_pipeline, self._csv(""))
        response = self.client.post(
            f"/api/v1/pipelines/{malformed_pipeline}/run"
        )
        self.assertEqual(response.status_code, 422)
        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=malformed_pipeline
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertEqual(
                run.error_message,
                "CSV input is empty or malformed.",
            )
        finally:
            session.close()

    def test_processing_failure_is_sanitized_and_finalized(self):
        pipeline_id = self._create_pipeline("processing-failure")
        self._create_source(pipeline_id, self._csv())
        response = self._execute(
            pipeline_id,
            patch(
                "app.quality.quality_engine.DataTransformation.transform",
                side_effect=RuntimeError("private file path and token"),
            ),
        )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private file path", response.text)
        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=pipeline_id
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertIsNotNone(run.finished_at)
            self.assertEqual(
                run.error_message,
                "Pipeline execution failed due to an internal error.",
            )
        finally:
            session.close()

    def test_quality_failure_persists_results_for_its_run_and_preserves_history(self):
        pipeline_id = self._create_pipeline("quality-history")
        configuration = {
            "data_quality": {
                "enabled": True,
                "rules": {"null_check": {"enabled": True}},
            }
        }
        self._create_source(
            pipeline_id,
            self._csv("name,value\nA,\nB,2\n"),
            configuration,
        )
        first_response = self.client.post(
            f"/api/v1/pipelines/{pipeline_id}/run"
        )
        self.assertEqual(first_response.status_code, 422)
        first_run_id = first_response.json()["detail"]["pipe_run_id"]
        first_run = self._get_run(first_run_id)
        self.assertEqual(first_run.status, PipelineStatus.FAILED)
        self.assertIsNotNone(first_run.finished_at)
        self.assertEqual(
            first_run.error_message,
            "Data Quality checks failed: 1 check(s) failed.",
        )

        results_response = self.client.get(
            f"/api/v1/pipeline-run-DQR/{first_run_id}"
        )
        self.assertEqual(results_response.status_code, 200)
        first_results = results_response.json()
        self.assertEqual(len(first_results), 1)
        self.assertEqual(first_results[0]["pipeline_run_id"], first_run_id)
        self.assertEqual(first_results[0]["check_name"], "NULL_check")
        self.assertFalse(first_results[0]["passed"])
        self.assertEqual(first_results[0]["rows_affected"], 1)

        session = self._session()
        try:
            source = session.query(DataSourceModel).filter_by(
                name=f"source-{pipeline_id}"
            ).one()
            source.location = self._csv()
            session.commit()
        finally:
            session.close()
        second_response = self._execute(pipeline_id)
        self.assertEqual(second_response.status_code, 200, second_response.text)
        second_run_id = second_response.json()["pipe_run_id"]
        self.assertNotEqual(first_run_id, second_run_id)

        first_results_again = self.client.get(
            f"/api/v1/pipeline-run-DQR/{first_run_id}"
        ).json()
        second_results = self.client.get(
            f"/api/v1/pipeline-run-DQR/{second_run_id}"
        ).json()
        self.assertEqual(first_results_again, first_results)
        self.assertEqual(len(second_results), 1)
        self.assertEqual(second_results[0]["pipeline_run_id"], second_run_id)
        self.assertTrue(second_results[0]["passed"])

    def test_metrics_counts_rates_and_incomplete_run_handling(self):
        pipeline_id = self._create_pipeline("metrics")
        other_pipeline_id = self._create_pipeline("other-metrics")
        base = datetime(2026, 1, 1, 12)
        self._create_run(
            pipeline_id,
            PipelineStatus.SUCCESS,
            base,
            base + timedelta(seconds=20),
        )
        self._create_run(
            pipeline_id,
            PipelineStatus.FAILED,
            base + timedelta(minutes=1),
            base + timedelta(minutes=1, seconds=10),
        )
        self._create_run(
            pipeline_id, PipelineStatus.SUCCESS, base + timedelta(minutes=2)
        )
        self._create_run(
            pipeline_id, PipelineStatus.RUNNING, base + timedelta(minutes=3)
        )
        self._create_run(
            pipeline_id,
            PipelineStatus.CANCELLED,
            base + timedelta(minutes=4),
            base + timedelta(minutes=4, seconds=1),
        )
        self._create_run(
            other_pipeline_id,
            PipelineStatus.FAILED,
            base + timedelta(hours=1),
            base + timedelta(hours=1, seconds=30),
        )

        response = self.client.get(
            f"/api/v1/pipelines/{pipeline_id}/metrics"
        )
        self.assertEqual(response.status_code, 200, response.text)
        metrics = response.json()
        self.assertEqual(metrics["pipeline_id"], pipeline_id)
        self.assertEqual(metrics["total_runs"], 5)
        self.assertEqual(metrics["successful_runs"], 2)
        self.assertEqual(metrics["failed_runs"], 1)
        self.assertEqual(metrics["running_runs"], 1)
        self.assertEqual(metrics["cancelled_runs"], 1)
        self.assertEqual(metrics["terminal_runs"], 2)
        self.assertEqual(metrics["success_rate"], 50.0)
        self.assertEqual(metrics["failure_rate"], 50.0)
        self.assertAlmostEqual(metrics["average_duration_seconds"], 15.0, places=3)
        self.assertEqual(metrics["latest_run_status"], PipelineStatus.CANCELLED.value)
        self.assertEqual(
            datetime.fromisoformat(metrics["latest_run_started_at"]),
            base + timedelta(minutes=4),
        )
        self.assertEqual(
            datetime.fromisoformat(metrics["latest_run_finished_at"]),
            base + timedelta(minutes=4, seconds=1),
        )
        self.assertEqual(
            datetime.fromisoformat(metrics["latest_successful_run_at"]),
            base + timedelta(seconds=20),
        )
        self.assertEqual(
            self.client.get("/api/v1/pipelines/2147483000/metrics").status_code,
            404,
        )

        empty_pipeline = self._create_pipeline("empty-metrics")
        empty_metrics = self.client.get(
            f"/api/v1/pipelines/{empty_pipeline}/metrics"
        ).json()
        self.assertEqual(empty_metrics["total_runs"], 0)
        self.assertEqual(empty_metrics["success_rate"], 0.0)
        self.assertEqual(empty_metrics["failure_rate"], 0.0)
        self.assertIsNone(empty_metrics["average_duration_seconds"])

    def test_metrics_exclude_missing_and_negative_durations(self):
        pipeline_id = self._create_pipeline("invalid-durations")
        base = datetime(2026, 1, 5, 12)
        self._create_run(
            pipeline_id,
            PipelineStatus.SUCCESS,
            base,
            base,
        )
        self._create_run(
            pipeline_id,
            PipelineStatus.FAILED,
            base + timedelta(minutes=1),
            base + timedelta(seconds=59),
        )
        self._create_run(
            pipeline_id,
            PipelineStatus.SUCCESS,
            base + timedelta(minutes=2),
        )

        response = self.client.get(
            f"/api/v1/pipelines/{pipeline_id}/metrics"
        )
        self.assertEqual(response.status_code, 200, response.text)
        metrics = response.json()
        self.assertEqual(metrics["terminal_runs"], 2)
        self.assertEqual(metrics["success_rate"], 50.0)
        self.assertEqual(metrics["failure_rate"], 50.0)
        self.assertEqual(metrics["average_duration_seconds"], 0.0)

    def test_quality_validation_and_storage_exceptions_fail_the_run(self):
        validation_pipeline = self._create_pipeline("validation-exception")
        configuration = {
            "data_quality": {
                "enabled": True,
                "rules": {"null_check": {"enabled": True}},
            }
        }
        self._create_source(validation_pipeline, self._csv(), configuration)
        with patch(
            "app.quality.quality_engine.DataValidator.check_missing_values",
            side_effect=ValueError("validator internal details"),
        ):
            response = self.client.post(
                f"/api/v1/pipelines/{validation_pipeline}/run"
            )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("validator internal details", response.text)
        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=validation_pipeline
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertEqual(
                run.error_message,
                "Pipeline execution failed due to an internal error.",
            )
            self.assertIsNotNone(run.finished_at)
            self.assertEqual(
                session.query(DataQualityResultModel)
                .filter_by(pipeline_run_id=run.id)
                .count(),
                0,
            )
        finally:
            session.close()

        storage_pipeline = self._create_pipeline("storage-exception")
        self._create_source(storage_pipeline, self._csv())
        response = self._execute(
            storage_pipeline,
            patch(
                "app.quality.quality_engine.ParquetStorage.save",
                side_effect=OSError("private storage path"),
            ),
        )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private storage path", response.text)
        session = self._session()
        try:
            run = session.query(PipelineRunModel).filter_by(
                pipeline_id=storage_pipeline
            ).one()
            self.assertEqual(run.status, PipelineStatus.FAILED)
            self.assertIsNotNone(run.finished_at)
            self.assertEqual(
                run.error_message,
                "Pipeline execution failed due to an internal error.",
            )
        finally:
            session.close()

    def test_history_pagination_scoping_and_run_ownership(self):
        pipeline_id = self._create_pipeline("history")
        other_pipeline_id = self._create_pipeline("other-history")
        base = datetime(2026, 2, 1, 12)
        old_run = self._create_run(
            pipeline_id,
            PipelineStatus.SUCCESS,
            base,
            base + timedelta(seconds=5),
        )
        tie_first = self._create_run(
            pipeline_id,
            PipelineStatus.FAILED,
            base + timedelta(hours=1),
            base + timedelta(hours=1, seconds=5),
        )
        tie_second = self._create_run(
            pipeline_id,
            PipelineStatus.SUCCESS,
            base + timedelta(hours=1),
            base + timedelta(hours=1, seconds=10),
        )
        other_run = self._create_run(
            other_pipeline_id,
            PipelineStatus.FAILED,
            base + timedelta(hours=2),
            base + timedelta(hours=2, seconds=5),
        )

        history = self.client.get(
            f"/api/v1/pipelines/{pipeline_id}/runs"
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual(
            [item["id"] for item in history.json()],
            [tie_second, tie_first, old_run],
        )
        self.assertTrue(
            all(item["pipeline_id"] == pipeline_id for item in history.json())
        )
        self.assertTrue(
            all("error_message" not in item for item in history.json())
        )
        page = self.client.get(
            f"/api/v1/pipelines/{pipeline_id}/runs?limit=1&offset=1"
        )
        self.assertEqual([item["id"] for item in page.json()], [tie_first])
        for query in ("limit=0", "limit=101", "offset=-1"):
            self.assertEqual(
                self.client.get(
                    f"/api/v1/pipelines/{pipeline_id}/runs?{query}"
                ).status_code,
                422,
            )

        self.assertEqual(
            self.client.get(
                f"/api/v1/pipelines/{pipeline_id}/runs/{old_run}"
            ).status_code,
            200,
        )
        individual_run = self.client.get(
            f"/api/v1/pipelines/{pipeline_id}/runs/{old_run}"
        ).json()
        self.assertNotIn("error_message", individual_run)
        self.assertEqual(
            self.client.get(
                f"/api/v1/pipelines/{pipeline_id}/runs/{other_run}"
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/pipelines/{pipeline_id}/runs/2147483000"
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/pipelines/2147483000/runs"
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/pipelines/{self._create_pipeline('empty-history')}/runs"
            ).json(),
            [],
        )

    def test_foreign_keys_and_no_duplicate_run_records(self):
        pipeline_id = self._create_pipeline("integrity")
        session = self._session()
        try:
            invalid_run = PipelineRunModel(
                pipeline_id=-1,
                status=PipelineStatus.PENDING,
                started_at=datetime.now(),
            )
            session.add(invalid_run)
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()

            invalid_quality_result = DataQualityResultModel(
                pipeline_run_id=-1,
                check_name="null_check",
                passed=False,
            )
            session.add(invalid_quality_result)
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()
        finally:
            session.close()

        self._create_source(pipeline_id, self._csv())
        response = self._execute(pipeline_id)
        self.assertEqual(response.status_code, 200, response.text)
        run_id = response.json()["pipe_run_id"]
        session = self._session()
        try:
            self.assertEqual(
                session.query(PipelineRunModel)
                .filter_by(pipeline_id=pipeline_id)
                .count(),
                1,
            )
            self.assertEqual(
                session.query(PipelineRunModel)
                .filter_by(id=run_id, pipeline_id=pipeline_id)
                .count(),
                1,
            )
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
