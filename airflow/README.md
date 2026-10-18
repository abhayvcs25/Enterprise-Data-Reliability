# Airflow infrastructure (Phase 9.1)

This directory contains an isolated Apache Airflow 2.10.5 development
environment. It does not alter the FastAPI service, its PostgreSQL database,
SQLAlchemy models, Alembic migrations, pipeline-run lifecycle, APIs, or
data-quality implementation. It defines no DAGs and does not call FastAPI.

## Compatibility and resource considerations

Airflow 2.10.5 lists Python 3.12 and PostgreSQL 16 among its tested
prerequisites. The `apache/airflow:2.10.5-python3.12` Docker Hub tag is active
and publishes Linux amd64 and arm64 images. See the
[Airflow 2.10.5 prerequisites](https://airflow.apache.org/docs/apache-airflow/2.10.5/installation/prerequisites.html)
and [Docker Hub image tag](https://hub.docker.com/r/apache/airflow/tags?name=2.10.5-python3.12).

This LocalExecutor setup requires three long-running services: the separate
Airflow metadata PostgreSQL database, the scheduler, and the webserver. A
one-shot initializer migrates Airflow's metadata schema. LocalExecutor runs
task worker processes from the scheduler, not in a separate worker container;
parallelism is capped at two task processes. A triggerer is not included
because no deferrable tasks are configured in this phase.

Airflow's documentation recommends at least 4 GB of memory for Airflow, while
noting that actual needs vary by deployment. This is a baseline, not a
guarantee for this multi-service setup; task memory adds to the scheduler's
requirements. On an 8 GB machine with about 1.5 GB currently free, there is not
enough available headroom to safely start the stack alongside existing
workloads. Do not start containers until available memory has been reassessed
and adequate headroom is approved.

The metadata database is independent from the application's PostgreSQL
database: its host port is `5433` (container port `5432`), its volume is
`airflow-postgres-data`, and it is only published on `127.0.0.1`. The UI is
published on `127.0.0.1:8081`. No application database volume or host port is
referenced by this Compose project.

## Configure secrets

From the repository root, copy the template and replace all placeholder
values. The local file is ignored by Git:

```powershell
Copy-Item airflow\.env.example airflow\.env
```

Generate three different values using Python's standard library, then put
them in `airflow/.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use the first value for `AIRFLOW_DB_PASSWORD`, the base64 value for
`AIRFLOW_FERNET_KEY`, and the final value for
`AIRFLOW_WEBSERVER_SECRET_KEY`. Keep all generated values out of tracked files
and do not reuse the application's database credentials.

## Validate configuration

With the local `airflow/.env` populated, validate the Compose model from the
repository root:

```powershell
docker compose -f airflow/docker-compose.yaml config
```

This checks configuration only; it does not pull images or start containers.
The rendered output contains resolved credentials, so do not share or commit
it.

## Start only after resource approval

After confirming sufficient free memory and obtaining approval to run the
stack, initialize and start it with:

```powershell
docker compose -f airflow/docker-compose.yaml up -d
```

The initializer migrates Airflow's metadata database. Create the first local
Airflow admin user interactively after startup so its password is not stored
in Compose configuration or shell history:

```powershell
docker compose -f airflow/docker-compose.yaml exec airflow-webserver airflow users create --username admin --firstname Airflow --lastname Admin --role Admin --email admin@example.invalid
```

The CLI prompts for the user's password. The UI is then available at
<http://127.0.0.1:8081>. The database is reachable locally at
`127.0.0.1:5433`.

The named metadata database volume persists independently. Do not remove it
or use volume-removal commands as routine setup or cleanup.

## Official references

- [Airflow 2.10.5 prerequisites](https://airflow.apache.org/docs/apache-airflow/2.10.5/installation/prerequisites.html)
- [Airflow 2.10.5 LocalExecutor](https://airflow.apache.org/docs/apache-airflow/2.10.5/core-concepts/executor/local.html)
- [Airflow 2.10.5 Docker Compose guide](https://airflow.apache.org/docs/apache-airflow/2.10.5/howto/docker-compose/index.html)
- [Docker Hub: apache/airflow 2.10.5-python3.12](https://hub.docker.com/r/apache/airflow/tags?name=2.10.5-python3.12)
