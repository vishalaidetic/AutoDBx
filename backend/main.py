import os
from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File
from DataBricks.handler import (
    get_databricks_catalogs,
    get_databricks_schemas,
    get_databricks_tables,
    get_databricks_table_details,
    get_databricks_table_data, # Import the new function
)
from AutoDBx.handler import (
    # clone_and_cd_repository,
    databricks_validate,
    databricks_deploy,
    databricks_run_config_table_creation,
    databricks_run_migration_job,
)
from utils.cors import setup_cors
from utils.databricks_config_utils import store_databricks_config_from_csv, clear_databricks_session_config

from dotenv import load_dotenv
import os

from SourceDB.mongo_connect import connect_mongodb, fetch_data_mongodb, close_mongodb_connection
from pydantic import BaseModel
from typing import Optional, Dict, Any
from bson import ObjectId
from fastapi.responses import StreamingResponse

# Import the new file utility
from utils.file_utils import list_subdirectories

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Setup CORS middleware
setup_cors(app)


# Re-added MongoDBFetchRequest Pydantic model
class MongoDBFetchRequest(BaseModel):
    uri: Optional[str] = None # MongoDB Atlas URI, can be from .env or provided in request
    database_name: str
    collection_name: str
    query_filter: Dict[str, Any] = {}

    # Example of how to add validation if needed
    # @validator('uri', pre=True, always=True)
    # def check_uri_or_env(cls, v, values):
    #     if v is None and "MONGO_URI" not in os.environ:
    #         raise ValueError("MongoDB URI must be provided or set as MONGO_URI environment variable.")
    #     return v



@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI Backend!"}


@app.get("/databricks/catalogs")
async def get_catalogs():
    """
    Fetches a list of Unity Catalog catalogs from Databricks.
    """
    try:
        catalogs = get_databricks_catalogs()
        return {"catalogs": catalogs}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/databricks/schemas/{catalog_name}")
async def get_schemas_for_catalog(catalog_name: str):
    """
    Fetches schemas for a specified Unity Catalog catalog from Databricks.
    """
    try:
        schemas = get_databricks_schemas(catalog_name)
        return {"schemas": schemas}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/databricks/tables/{catalog_name}/{schema_name}")
async def get_tables_for_schema(catalog_name: str, schema_name: str):
    """
    Fetches tables for a specified Unity Catalog schema within a catalog from Databricks.
    """
    try:
        tables = get_databricks_tables(catalog_name, schema_name)
        return {"tables": tables}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/databricks/tables/{catalog_name}/{schema_name}/{table_name}/details")
async def get_table_details(catalog_name: str, schema_name: str, table_name: str):
    """
    Fetches details for a specific table in a Unity Catalog schema within a catalog from Databricks.
    """
    try:
        table_details = get_databricks_table_details(catalog_name, schema_name, table_name)
        return {"table_details": table_details}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/databricks/tables/{catalog_name}/{schema_name}/{table_name}/data")
async def get_table_data(catalog_name: str, schema_name: str, table_name: str):
    """
    Fetches sample data for a specific table in a Unity Catalog schema within a catalog from Databricks.
    """
    try:
        table_data = get_databricks_table_data(catalog_name, schema_name, table_name)
        print("table_data_vishal",table_data)
        return {"table_data": table_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# @app.post("/github/clone")
# async def clone_repository(repo_url: str = Query(...), base_dir: str = Query("/tmp"), branch: Optional[str] = Query(None)): # Corrected branch type hint
#     try:
#         msg = clone_and_cd_repository(repo_url, base_dir, branch)
#         return {"message": msg}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/databricks/validate")
async def validate_bundle(project_name: str = Query(..., description="The name of the AutoDBx project to validate")):
    return databricks_validate(project_name)


@app.get("/databricks/deploy")
async def deploy_bundle(project_name: str = Query(..., description="The name of the AutoDBx project to deploy")):
    return databricks_deploy(project_name)


@app.get("/databricks/run/config-table")
async def run_config_table(project_name: str = Query(..., description="The name of the AutoDBx project to run config table creation for")):
    return databricks_run_config_table_creation(project_name)


@app.get("/databricks/run/migration-job")
async def run_migration_job(project_name: str = Query(..., description="The name of the AutoDBx project to run migration job for")):
    return databricks_run_migration_job(project_name)


@app.post("/databricks/upload-config")
async def upload_databricks_config(file: UploadFile = File(...)):
    """
    Uploads a CSV file containing Databricks instance, access token, and SQL Warehouse ID.
    These credentials will be used for the current session.
    """
    try:
        csv_content = (await file.read()).decode("utf-8")
        store_databricks_config_from_csv(csv_content)
        return {"message": "Databricks configuration uploaded and stored successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/data/mongodb")
async def get_mongodb_data(request_body: MongoDBFetchRequest): # Corrected type hint
    # Prioritize URI from request body, fallback to environment variable
    mongo_uri = request_body.uri or os.getenv("MONGO_URI") 

    if not mongo_uri:
        raise HTTPException(status_code=400, detail="MongoDB URI not provided in request or as MONGO_URI environment variable.")

    database_name = request_body.database_name
    collection_name = request_body.collection_name
    query_filter = request_body.query_filter

    client = None
    try:
        db = connect_mongodb(mongo_uri, database_name=database_name)
        
        if db:
            result = fetch_data_mongodb(db, collection_name, query_filter)

            if result:
                for doc in result:
                    if '_id' in doc and isinstance(doc['_id'], ObjectId):
                        doc['_id'] = str(doc['_id'])
            return {"data": result}
        else:
            raise HTTPException(status_code=500, detail="Could not connect to MongoDB or select database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from MongoDB: {e}")
    finally:
        if db and hasattr(db, 'client'):
            close_mongodb_connection(db.client)
        elif client:
            close_mongodb_connection(client)

@app.get("/autodbx/folders") 
async def get_autodbx_folders():
    """
    Fetches the list of subdirectories within the AutoDBx folder for cloning destinations.
    """
    # Construct the path to the Data_Visualization/AutoDBx folder
    # This assumes the backend is run from within the 'backend' directory.
    # os.path.abspath(os.path.join(os.getcwd(), os.pardir)) goes up one level to Data_Visualization
    # then os.path.join(..., "AutoDBx") goes into the AutoDBx folder
    autodbx_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir, "AutoDBx"))

    if not os.path.isdir(autodbx_path):
        raise HTTPException(status_code=404, detail=f"AutoDBx directory not found at {autodbx_path}")
    try:
        folders = list_subdirectories(autodbx_path)
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AutoDBx folders: {e}")