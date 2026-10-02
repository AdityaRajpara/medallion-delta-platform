"""Optional Airflow orchestration example. Install package in the Airflow image."""
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(dag_id="treasury_medallion_local", description="Open Treasury rates through Bronze, Silver, and Gold",
         start_date=datetime(2025, 1, 1), schedule="@daily", catchup=False,
         default_args={"retries": 2}, tags=["portfolio", "medallion", "treasury"]) as dag:
    BashOperator(task_id="ingest_transform_publish",
                 bash_command="medallion run --source treasury --config config/local.json")
