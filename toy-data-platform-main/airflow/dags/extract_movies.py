from __future__ import annotations

import os
from datetime import datetime

from airflow import models
from airflow.providers.docker.operators.docker import DockerOperator

DAG_ID = "extract_movies"

DATASETS = ["imdb_top_1000", "meta_critic", "netflix_titles"]


env_vars = {
    "DESTINATION__FILESYSTEM__BUCKET_URL": "s3://raw",
    "DESTINATION__FILESYSTEM__CREDENTIALS__ENDPOINT_URL": "http://minio:9000",
    "DESTINATION__FILESYSTEM__CREDENTIALS__REGION_NAME": "us-east-1",
    "DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID": str(
        os.environ.get("DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID")
    ),
    "DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY": str(
        os.environ.get("DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY")
    ),
    "NORMALIZE__LOADER_FILE_FORMAT": "parquet",
    "PYICEBERG_CATALOG__RAW__URI": "http://lakekeeper:8181/catalog",
    "PYICEBERG_CATALOG__RAW__WAREHOUSE": "raw",
    "ICEBERG_CATALOG__ICEBERG_CATALOG_NAME": "raw",
    "ICEBERG_CATALOG__ICEBERG_CATALOG_TYPE": "rest",
}

with models.DAG(
    DAG_ID,
    schedule="@once",
    start_date=datetime(2025, 2, 1),
    catchup=False,
    max_active_tasks=2,
    tags=["movies", "full", "dbt"],
) as dag:
    ingestion_tasks = [
        DockerOperator(
            docker_url="unix://var/run/docker.sock",
            image="my-dlt-pipeline:latest",
            command=["python", "filesystem_pipeline.py", "-t", dataset],
            network_mode="container:airflow_scheduler",
            task_id=f"ingestion-movies-{dataset}",
            auto_remove="force",
            retries=1,
            dag=dag,
            environment={**env_vars},
        )
        for dataset in DATASETS
    ]

    dbt_build_task = DockerOperator(
        docker_url="unix://var/run/docker.sock",
        image="movies_transform:latest",
        command=["dbt", "build", "--no-partial-parse", "--target-path", "target/prod"],
        network_mode="container:airflow_scheduler",
        task_id="transform-dbt-build",
        auto_remove="force",
        retries=1,
        dag=dag,
        environment={"DBT_PARTIAL_PARSE": "false"},
    )

    ingestion_tasks >> dbt_build_task
