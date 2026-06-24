import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

DATA_PATH = Path(__file__).resolve().parent.parent / "data"
REQUIRED_ENV_VARS = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            payload.update(record.extra_data)
        return json.dumps(payload, ensure_ascii=True)


def get_logger() -> logging.Logger:
    logger = logging.getLogger("analytics_ingestion")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, level: int, event: str, **extra_data) -> None:
    logger.log(level, event, extra={"extra_data": extra_data})


def normalize_columns(columns: pd.Index) -> pd.Index:
    return columns.str.strip().str.lower().str.replace(" ", "_", regex=False)


def validate_env_vars() -> None:
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        missing = ", ".join(missing_vars)
        raise RuntimeError(f"Missing required environment variables: {missing}")


def build_engine():
    db_url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(db_url)


def load_postgres(engine, csv_path: Path, table_name: str, logger: logging.Logger) -> None:
    df = pd.read_csv(csv_path)
    df.columns = normalize_columns(df.columns)
    with engine.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        df.to_sql(table_name, conn, if_exists="append", index=False)
    log_event(
        logger,
        logging.INFO,
        "table_loaded",
        table_name=table_name,
        file_name=csv_path.name,
        rows_loaded=len(df),
    )


def main() -> None:
    logger = get_logger()
    log_event(logger, logging.INFO, "ingestion_started", data_path=str(DATA_PATH))

    validate_env_vars()

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data path does not exist: {DATA_PATH}")

    csv_files = sorted(path for path in DATA_PATH.iterdir() if path.suffix.lower() == ".csv")
    if not csv_files:
        raise RuntimeError(f"No CSV files found in data path: {DATA_PATH}")

    engine = build_engine()
    failed_files: list[str] = []

    for csv_path in csv_files:
        table_name = f"raw_{csv_path.stem}"
        log_event(
            logger,
            logging.INFO,
            "table_loading",
            table_name=table_name,
            file_name=csv_path.name,
        )
        try:
            load_postgres(engine, csv_path, table_name, logger)
        except Exception as exc:
            log_event(
                logger,
                logging.ERROR,
                "table_load_failed",
                table_name=table_name,
                file_name=csv_path.name,
                error=str(exc),
            )
            failed_files.append(csv_path.name)

    total = len(csv_files)
    succeeded = total - len(failed_files)
    log_event(
        logger,
        logging.INFO,
        "ingestion_finished",
        files_processed=total,
        succeeded=succeeded,
        failed=len(failed_files),
    )

    if failed_files:
        raise RuntimeError(f"Ingestion completed with {len(failed_files)} failure(s): {failed_files}")


if __name__ == "__main__":
    main()
