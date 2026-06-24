from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

INGEST_CMD = r"""
set -eEuo pipefail

GREEN_LIGHT='\033[92m'
GREEN_DARK='\033[32m'
RED='\033[31m'
PURPLE='\033[35m'
HIGHLIGHT='\033[96m'
NC='\033[0m'

on_error() {
  code=$?
  echo -e "${RED}[ERROR] task=ingest_csv exit_code=${code} ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
  exit $code
}

on_stopped() {
  echo -e "${PURPLE}[STOPPED] task=ingest_csv ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
  exit 143
}

trap on_error ERR
trap on_stopped SIGINT SIGTERM

echo -e "${GREEN_LIGHT}[RUN] task=ingest_csv ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
cd /opt/project
python src/load_data.py
echo -e "${GREEN_DARK}[SUCCESS] task=ingest_csv ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
"""

DBT_RUN_CMD = r"""
set -eEuo pipefail

GREEN_LIGHT='\033[92m'
GREEN_DARK='\033[32m'
RED='\033[31m'
PURPLE='\033[35m'
HIGHLIGHT='\033[96m'
NC='\033[0m'

on_error() {
  code=$?
  echo -e "${RED}[ERROR] task=dbt_run exit_code=${code} ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
  exit $code
}

on_stopped() {
  echo -e "${PURPLE}[STOPPED] task=dbt_run ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
  exit 143
}

trap on_error ERR
trap on_stopped SIGINT SIGTERM

echo -e "${GREEN_LIGHT}[RUN] task=dbt_run ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
cd /opt/project/analytics_dbt
dbt run --profiles-dir /opt/project/analytics_dbt
echo -e "${GREEN_DARK}[SUCCESS] task=dbt_run ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
echo -e "${GREEN_DARK}[SUCCESS] dbt_artifacts run_results=${HIGHLIGHT}/opt/project/analytics_dbt/target/run_results.json${NC} manifest=${HIGHLIGHT}/opt/project/analytics_dbt/target/manifest.json${NC}"
"""

DBT_TEST_CMD = r"""
set -eEuo pipefail

GREEN_LIGHT='\033[92m'
GREEN_DARK='\033[32m'
RED='\033[31m'
PURPLE='\033[35m'
HIGHLIGHT='\033[96m'
NC='\033[0m'

on_error() {
  code=$?
  echo -e "${RED}[ERROR] task=dbt_test exit_code=${code} ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
  exit $code
}

on_stopped() {
  echo -e "${PURPLE}[STOPPED] task=dbt_test ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
  exit 143
}

trap on_error ERR
trap on_stopped SIGINT SIGTERM

echo -e "${GREEN_LIGHT}[RUN] task=dbt_test ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
cd /opt/project/analytics_dbt
dbt test --profiles-dir /opt/project/analytics_dbt
echo -e "${GREEN_DARK}[SUCCESS] task=dbt_test ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
echo -e "${GREEN_DARK}[SUCCESS] dbt_artifacts run_results=${HIGHLIGHT}/opt/project/analytics_dbt/target/run_results.json${NC} manifest=${HIGHLIGHT}/opt/project/analytics_dbt/target/manifest.json${NC}"
"""

with DAG(
    dag_id="analytics_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    ingest = BashOperator(
        task_id="ingest_csv",
        bash_command=INGEST_CMD,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=DBT_RUN_CMD,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=DBT_TEST_CMD,
    )

    ingest >> dbt_run >> dbt_test
