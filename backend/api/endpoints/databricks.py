from fastapi import APIRouter, File, HTTPException, UploadFile
from service.databricks import (
    get_databricks_catalogs,
    get_databricks_schemas,
    get_databricks_table_data,
    get_databricks_table_details,
    get_databricks_tables,
    store_databricks_config_from_csv,
)
from utils.custom_reponse import custom_response

router = APIRouter(prefix="/databricks", tags=["databricks"])


@router.get("/catalogs")
async def get_catalogs():
    """
    Fetches a list of Unity Catalog catalogs from Databricks.
    """
    try:
        catalogs = get_databricks_catalogs()
        return custom_response(
            success=True,
            message="Catalogs fetched successfully",
            data={"catalogs": catalogs},
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=400)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/schemas/{catalog_name}")
async def get_schemas_for_catalog(catalog_name: str):
    """
    Fetches schemas for a specified Unity Catalog catalog from Databricks.
    """
    try:
        schemas = get_databricks_schemas(catalog_name)
        return custom_response(
            success=True,
            message=f"Schemas for {catalog_name} fetched successfully",
            data={"schemas": schemas},
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=400)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/tables/{catalog_name}/{schema_name}")
async def get_tables_for_schema(catalog_name: str, schema_name: str):
    """
    Fetches tables for a specified Unity Catalog schema within a catalog from Databricks.
    """
    try:
        tables = get_databricks_tables(catalog_name, schema_name)
        return custom_response(
            success=True,
            message=f"Tables for {catalog_name}.{schema_name} fetched successfully",
            data={"tables": tables},
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=400)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/tables/{catalog_name}/{schema_name}/{table_name}/details")
async def get_table_details(catalog_name: str, schema_name: str, table_name: str):
    """
    Fetches details for a specific table in a Unity Catalog schema within a catalog from Databricks.
    """
    try:
        table_details = get_databricks_table_details(
            catalog_name, schema_name, table_name
        )
        return custom_response(
            success=True,
            message=f"Details for {catalog_name}.{schema_name}.{table_name} fetched successfully",
            data={"table_details": table_details},
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=400)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.get("/tables/{catalog_name}/{schema_name}/{table_name}/data")
async def get_table_data(catalog_name: str, schema_name: str, table_name: str):
    """
    Fetches sample data for a specific table in a Unity Catalog schema within a catalog from Databricks.
    """
    try:
        table_data = get_databricks_table_data(catalog_name, schema_name, table_name)
        return custom_response(
            success=True,
            message=f"Data for {catalog_name}.{schema_name}.{table_name} fetched successfully",
            data={"table_data": table_data},
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=400)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)


@router.post("/upload-config")
async def upload_databricks_config(file: UploadFile = File(...)):
    """
    Uploads a CSV file containing Databricks instance, access token, and SQL Warehouse ID.
    These credentials will be used for the current session.
    """
    try:
        csv_content = (await file.read()).decode("utf-8")
        store_databricks_config_from_csv(csv_content)
        return custom_response(
            success=True,
            message="Databricks configuration uploaded and stored successfully.",
            status=200,
        )
    except ValueError as e:
        return custom_response(success=False, message=str(e), status=400)
    except RuntimeError as e:
        return custom_response(success=False, message=str(e), status=500)
    except Exception as e:
        return custom_response(success=False, message=str(e), status=500)
