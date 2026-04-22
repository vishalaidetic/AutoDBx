import { Catalog, DatabricksTable, DatabricksTableDataResponse, DatabricksTableDetails, Schema } from './modal';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const baseURL = `${API_BASE}/api/databricks`;

export interface ServiceResponse<T> {
  data: T | null;
  error: string | null;
}

export const fetchDatabricksCatalogs = async (): Promise<ServiceResponse<Catalog[]>> => {
  try {
    const response = await fetch(`${baseURL}/catalogs`);
    const resData = await response.json();
    if (resData?.success) {
      return { data: resData?.data?.catalogs || [], error: null };
    } else {
      return { data: null, error: resData?.message || `HTTP ${response.status}` };
    }
  } catch (error: any) {
    return { data: null, error: error.message };
  }
}

export const fetchDatabricksSchemasForCatalog = async (catalogName: string): Promise<ServiceResponse<Schema[]>> => {
  try {
    const response = await fetch(`${baseURL}/schemas/${catalogName}`);
    const resData = await response.json();
    if (resData?.success) {
      return { data: resData?.data?.schemas || [], error: null };
    } else {
      return { data: null, error: resData?.message || `HTTP ${response.status}` };
    }
  } catch (error: any) {
    return { data: null, error: error.message };
  }
}

export const fetchDatabricksTablesForSchema = async (
  catalogName: string,
  schemaName: string
): Promise<ServiceResponse<DatabricksTable[]>> => {
  try {
    const response = await fetch(`${baseURL}/tables/${encodeURIComponent(catalogName)}/${encodeURIComponent(schemaName)}`);
    const resData = await response.json();
    if (resData?.success) {
      return { data: resData?.data?.tables || [], error: null };
    } else {
      return { data: null, error: resData?.message || `HTTP ${response.status}` };
    }
  } catch (error: any) {
    return { data: null, error: error.message };
  }
}

export const fetchDatabricksTableDetails = async (
  catalogName: string,
  schemaName: string,
  tableName: string
): Promise<ServiceResponse<DatabricksTableDetails>> => {
  try {
    const response = await fetch(`${baseURL}/tables/${encodeURIComponent(catalogName)}/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}/details`);
    const resData = await response.json();
    if (resData?.success) {
      return { data: resData?.data?.table_details || null, error: null };
    } else {
      return { data: null, error: resData?.message || `HTTP ${response.status}` };
    }
  } catch (error: any) {
    return { data: null, error: error.message };
  }
}

export const fetchDatabricksTableData = async (
  catalogName: string,
  schemaName: string,
  tableName: string
): Promise<ServiceResponse<DatabricksTableDataResponse>> => {
  try {
    const response = await fetch(`${baseURL}/tables/${encodeURIComponent(catalogName)}/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}/data`);
    const resData = await response.json();
    if (resData?.success) {
      const rawData = resData?.data?.table_data;

      // 1. New format: { columns: [...], data: [...] }
      if (
        rawData &&
        typeof rawData === 'object' &&
        !Array.isArray(rawData) &&
        Array.isArray(rawData.columns) &&
        Array.isArray(rawData.data)
      ) {
        return { data: rawData as DatabricksTableDataResponse, error: null };
      }

      // 2. Legacy format: [ {col1: val, col2: val}, ... ]
      if (Array.isArray(rawData)) {
        const columns = rawData.length > 0 ? Object.keys(rawData[0]) : [];
        return {
          data: { columns, data: rawData },
          error: null
        };
      }
      return { data: null, error: "Unexpected table data format" };
    } else {
      return { data: null, error: resData?.message || `HTTP ${response.status}` };
    }
  } catch (error: any) {
    return { data: null, error: error.message };
  }
}