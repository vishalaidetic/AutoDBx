from io import StringIO
from typing import Dict, Optional

import pandas as pd

_databricks_session_configs: Dict[str, str] = {}


def store_databricks_config_from_csv(csv_content: str) -> None:
    """
    Parses a CSV string, extracts Databricks configuration, and stores it in memory.
    Expected CSV columns: DATABRICKS_INSTANCE, DATABRICKS_ACCESS_TOKEN, DATABRICKS_SQL_WAREHOUSE_ID
    """
    global _databricks_session_configs

    try:
        df = pd.read_csv(StringIO(csv_content))

        required_columns = [
            "DATABRICKS_INSTANCE",
            "DATABRICKS_ACCESS_TOKEN",
            "DATABRICKS_SQL_WAREHOUSE_ID",
        ]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(
                f"CSV must contain all required columns: {', '.join(required_columns)}"
            )

        # Assuming only one row of configuration for simplicity
        config_row = df.iloc[0]

        _databricks_session_configs["DATABRICKS_INSTANCE"] = config_row[
            "DATABRICKS_INSTANCE"
        ]
        _databricks_session_configs["DATABRICKS_ACCESS_TOKEN"] = config_row[
            "DATABRICKS_ACCESS_TOKEN"
        ]
        _databricks_session_configs["DATABRICKS_SQL_WAREHOUSE_ID"] = config_row[
            "DATABRICKS_SQL_WAREHOUSE_ID"
        ]

    except Exception as e:
        clear_databricks_session_config()  # Clear any partial config on error
        raise RuntimeError(f"Failed to process Databricks config CSV: {e}")


def get_databricks_session_config(key: str) -> Optional[str]:
    """
    Retrieves a specific Databricks configuration value from the session store.
    """
    return _databricks_session_configs.get(key)


def clear_databricks_session_config() -> None:
    """
    Clears all stored Databricks configuration for the current session.
    """
    global _databricks_session_configs
    _databricks_session_configs = {}
