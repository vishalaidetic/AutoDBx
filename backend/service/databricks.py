import os
from typing import Any, Dict, List, Optional

import requests
from databricks import sql
from dotenv import load_dotenv
from fastapi import HTTPException
from utils.databricks_config_utils import (
    get_databricks_session_config,
    store_databricks_config_from_csv,
)

load_dotenv()


def _get_databricks_credential(key: str) -> Optional[str]:
    """
    Helper to get Databricks credential, prioritizing session config over environment variables.
    """
    return get_databricks_session_config(key) or os.getenv(key)


def get_databricks_catalogs() -> List[Dict[str, Any]]:
    """
    Fetches a list of Unity Catalog catalogs from Databricks.
    """
    DATABRICKS_INSTANCE = _get_databricks_credential("DATABRICKS_INSTANCE")
    DATABRICKS_ACCESS_TOKEN = _get_databricks_credential("DATABRICKS_ACCESS_TOKEN")

    if not DATABRICKS_INSTANCE or not DATABRICKS_ACCESS_TOKEN:
        print(DATABRICKS_INSTANCE, "DATABRICKS_INSTANCE Vishal")
        raise ValueError("Databricks instance URL or Access Token not provided.")

    url = f"{DATABRICKS_INSTANCE}/api/2.1/unity-catalog/catalogs"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    catalogs_data = response.json().get("catalogs", [])
    return catalogs_data


def get_databricks_schemas(catalog_name: str) -> List[Dict[str, Any]]:
    """
    Fetches schemas for a specified Unity Catalog catalog from Databricks.
    """
    DATABRICKS_INSTANCE = _get_databricks_credential("DATABRICKS_INSTANCE")
    DATABRICKS_ACCESS_TOKEN = _get_databricks_credential("DATABRICKS_ACCESS_TOKEN")

    if not DATABRICKS_INSTANCE or not DATABRICKS_ACCESS_TOKEN:
        raise ValueError("Databricks instance URL or Access Token not provided.")

    url = f"{DATABRICKS_INSTANCE}/api/2.1/unity-catalog/schemas"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    params = {"catalog_name": catalog_name}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    schemas_data = response.json().get("schemas", [])
    return schemas_data


def get_databricks_tables(catalog_name: str, schema_name: str) -> List[Dict[str, Any]]:
    """
    Fetches tables for a specified Unity Catalog schema within a catalog from Databricks.
    """
    DATABRICKS_INSTANCE = _get_databricks_credential("DATABRICKS_INSTANCE")
    DATABRICKS_ACCESS_TOKEN = _get_databricks_credential("DATABRICKS_ACCESS_TOKEN")

    if not DATABRICKS_INSTANCE or not DATABRICKS_ACCESS_TOKEN:
        raise ValueError("Databricks instance URL or Access Token not provided.")

    url = f"{DATABRICKS_INSTANCE}/api/2.1/unity-catalog/tables"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    params = {"catalog_name": catalog_name, "schema_name": schema_name}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    tables_data = response.json().get("tables", [])
    return tables_data


def get_databricks_table_details(
    catalog_name: str, schema_name: str, table_name: str
) -> Dict[str, Any]:
    """
    Fetches details for a specific table in a Unity Catalog schema within a catalog from Databricks.
    """
    DATABRICKS_INSTANCE = _get_databricks_credential("DATABRICKS_INSTANCE")
    DATABRICKS_ACCESS_TOKEN = _get_databricks_credential("DATABRICKS_ACCESS_TOKEN")

    if not DATABRICKS_INSTANCE or not DATABRICKS_ACCESS_TOKEN:
        raise ValueError("Databricks instance URL or Access Token not provided.")

    table_identifier = f"{catalog_name}.{schema_name}.{table_name}"
    url = f"{DATABRICKS_INSTANCE}/api/2.1/unity-catalog/tables/{table_identifier}"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_databricks_table_data(
    catalog_name: str, schema_name: str, table_name: str
) -> Dict[str, Any]:
    """
    Fetches sample data for a specific table using Databricks SQL Warehouse.
    """
    DATABRICKS_INSTANCE = _get_databricks_credential("DATABRICKS_INSTANCE")
    DATABRICKS_ACCESS_TOKEN = _get_databricks_credential("DATABRICKS_ACCESS_TOKEN")
    DATABRICKS_SQL_WAREHOUSE_ID = _get_databricks_credential(
        "DATABRICKS_SQL_WAREHOUSE_ID"
    )

    if (
        not DATABRICKS_INSTANCE
        or not DATABRICKS_ACCESS_TOKEN
        or not DATABRICKS_SQL_WAREHOUSE_ID
    ):
        raise ValueError(
            "Databricks instance URL, Access Token, or SQL Warehouse ID not provided."
        )

    # Extract hostname from instance URL
    server_hostname = DATABRICKS_INSTANCE.replace("https://", "").replace("http://", "")
    http_path = f"/sql/1.0/warehouses/{DATABRICKS_SQL_WAREHOUSE_ID}"
    access_token = DATABRICKS_ACCESS_TOKEN

    table_full_name = f"{catalog_name}.{schema_name}.{table_name}"
    query = f"SELECT * FROM {table_full_name} LIMIT 100"  # Fetching top 100 rows

    data = []
    with sql.connect(
        server_hostname=server_hostname, http_path=http_path, access_token=access_token
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            # Convert Row objects to dictionaries
            columns = [desc[0] for desc in cursor.description]
            for row in result:
                data.append(dict(zip(columns, row)))
    return {"columns": columns, "data": data}
