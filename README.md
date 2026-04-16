# Data Visualization & Migration Backend

This backend serves as the orchestration layer for managing Databricks Unity Catalog data exploration and automated migrations using the AutoDBx framework.

## Backend Architecture & Flow

The backend is built with **FastAPI** and follows a modular design to handle different aspects of the data lifecycle.

### 1. Request Entry & Middleware
- **Entry Point**: `main.py` initializes the FastAPI application.
- **CORS Handling**: `utils/cors.py` manages cross-origin resource sharing to allow interaction with the frontend.
- **Config Management**: `utils/databricks_config_utils.py` provides an in-memory store for session-based Databricks credentials, allowing users to dynamiclly switch environments.

### 2. AutoDBx Orchestration Flow
The most critical part of the backend is its interaction with Databricks Asset Bundles (DABs):
1. **Selection**: The user selects a migration project (e.g., `mysql_migration`) from the `AutoDBx/` root folder.
2. **Path Resolution**: `AutoDBx/handler.py` resolves the absolute path to the selected bundle.
3. **Execution**: The backend uses Python's `subprocess` to trigger the **Databricks CLI**.
4. **Streaming**: Commands are executed via a generator that yields output in real-time. This is streamed to the user via `StreamingResponse`, providing a live console experience for:
   - `bundle validate`
   - `bundle deploy`
   - `bundle run config_table_creation`
   - `bundle run migration_job`

### 3. Databricks Integration Flow
The backend provides a discovery layer for Databricks resources:
1. **Workspace API**: `DataBricks/handler.py` uses the Databricks REST API to list Catalogs, Schemas, and Tables.
2. **SQL Execution**: It utilizes the `databricks-sql-connector` to sample data from target tables after migration, providing immediate verification of successful data transfer.

### 4. Source Database Connectivity
- Connectors in `SourceDB/` (like `mongo_connect.py`) allow the backend to fetch metadata and sample documents from source systems.
- This allows users to preview their data before initializing a migration through the AutoDBx framework.

---

## API Endpoints Summary

| Category | Endpoint | Description |
| :--- | :--- | :--- |
| **Config** | `POST /databricks/upload-config` | Upload session-based credentials. |
| **Discovery** | `GET /autodbx/folders` | List available migration projects. |
| **Exploration** | `GET /databricks/catalogs` | List all available Unity Catalogs. |
| **Automation** | `GET /databricks/deploy` | Deploy a DAB to Databricks. |
| **Execution** | `GET /databricks/run/migration-job` | Trigger the migration pipeline. |
| **Source** | `POST /data/mongodb` | Preview data from a MongoDB source. |

## Sequence of Operations for a Migration
1. **Initialize Session**: Client uploads Databricks credentials via `/upload-config`.
2. **Select Bundle**: Client fetches available projects via `/autodbx/folders`.
3. **Deploy Bundle**: Client triggers `/databricks/deploy`.
4. **Setup Config**: Client runs `/databricks/run/config-table` to initialize the migration metadata.
5. **Run Migration**: Client starts the full pipeline via `/databricks/run/migration-job`.
6. **Verify Data**: Client uses `/databricks/tables/.../data` to confirm the data landed in the target Unity Catalog table.
