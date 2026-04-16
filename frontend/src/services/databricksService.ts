import { Catalog, Schema, DatabricksTable, DatabricksTableDetails, DatabricksTableDataResponse} from './modal';
  
export async function fetchDatabricksCatalogs(): Promise<Catalog[]> {
    try {
    //   }
      const response = await fetch(`http://127.0.0.1:8000/databricks/catalogs`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.catalogs.catalogs; // Access the nested 'catalogs' array
    } catch (error) {
      console.error("Error fetching Databricks catalogs:", error);
      return [];
    }
  }
  
  
// New function to fetch Databricks Schemas for a given catalog
export async function fetchDatabricksSchemasForCatalog(catalogName: string): Promise<Schema[]> {
    try {
      const response = await fetch(`http://127.0.0.1:8000/databricks/schemas/${catalogName}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.schemas.schemas; // Access the nested 'schemas' array
    } catch (error) {
      console.error(`Error fetching Databricks schemas for catalog ${catalogName}:`, error);
      return [];
    }
  }

// Service to fetch Databricks tables for a given catalog and schema
export async function fetchDatabricksTablesForSchema(
    catalogName: string,
    schemaName: string
  ): Promise<DatabricksTable[]> {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/databricks/tables/${encodeURIComponent(catalogName)}/${encodeURIComponent(schemaName)}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      let tables: any = [];

      if (Array.isArray(data?.tables)) {
        tables = data.tables;
      } else if (data?.tables && Array.isArray(data.tables.tables)) {
        tables = data.tables.tables;
      } else {
        tables = [];
      }

      // Defensive: ensure each table is an object
      if (!Array.isArray(tables)) {
        tables = [];
      }

      return tables;
    } catch (error) {
      console.error(
        `Error fetching Databricks tables for catalog ${catalogName}, schema ${schemaName}:`,
        error
      );
      return [];
    }
  }

// Service to fetch Databricks table details for a given catalog, schema, and table
export async function fetchDatabricksTableDetails(
    catalogName: string,
    schemaName: string,
    tableName: string
  ): Promise<DatabricksTableDetails | null> {
    try {
      const url = `http://127.0.0.1:8000/databricks/tables/${encodeURIComponent(
        catalogName
      )}/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}/details`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // The backend returns { table_details: {...} }
      // Defensive: ensure we return an object or null, and allow for missing fields
      if (data && typeof data.table_details === 'object' && data.table_details !== null) {
        return data.table_details as DatabricksTableDetails;
      }
      return null;
    } catch (error) {
      console.error(
        `Error fetching Databricks table details for catalog ${catalogName}, schema ${schemaName}, table ${tableName}:`,
        error
      );
      return null;
    }
  }

export async function fetchDatabricksTableData(
    catalogName: string,
    schemaName: string,
    tableName: string
  ): Promise<DatabricksTableDataResponse | null> {
    try {
      const url = `http://127.0.0.1:8000/databricks/tables/${encodeURIComponent(
        catalogName
      )}/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}/data`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // The backend returns { table_data: { columns: [...], data: [...] } }
      if (
        data &&
        typeof data.table_data === 'object' &&
        data.table_data !== null &&
        Array.isArray(data.table_data.columns) &&
        Array.isArray(data.table_data.data)
      ) {
        return data.table_data as DatabricksTableDataResponse;
      }
      return null;
    } catch (error) {
      console.error(
        `Error fetching Databricks table data for catalog ${catalogName}, schema ${schemaName}, table ${tableName}:`,
        error
      );
      return null;
    }
  }