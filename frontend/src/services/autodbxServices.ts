const API_BASE = import.meta.env.VITE_API_BASE_URL;
const baseURL = `${API_BASE}/api`;

export interface MigrationCreate {
    description?: string;
    source_csv_id?: string;
}

export interface StepStatus {
    status: string;
    meta_data?: any;
    start_time?: string;
    completion_time?: string;
}

export interface MigrationResponse {
    id: string;
    description: string;
    status: string;
    source_csv_id: string;
    validate_bundle: StepStatus;
    deploy_bundle: StepStatus;
    config_table: StepStatus;
    migration_job: StepStatus;
    created_at: string;
    updated_at: string;
}

export interface ServiceResponse<T> {
    data: T | null;
    error: string | null;
}

// --- Migration Service ---

export const createMigration = async (data: MigrationCreate): Promise<ServiceResponse<MigrationResponse>> => {
    try {
        const response = await fetch(`${baseURL}/migrations/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const getMigration = async (id: string): Promise<ServiceResponse<MigrationResponse>> => {
    try {
        const response = await fetch(`${baseURL}/migrations/${id}`);
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const runMigrationStep = async (id: string, stepKey: string, projectName: string): Promise<ServiceResponse<MigrationResponse>> => {
    try {
        const response = await fetch(`${baseURL}/migrations/${id}/run/${stepKey}?project_name=${projectName}`, {
            method: 'POST',
        });
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const fetchAutodbxFolders = async (): Promise<ServiceResponse<{ folders: string[] }>> => {
    try {
        const response = await fetch(`${baseURL}/migrations/folders`);
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

// --- Databricks Service ---

export const uploadDatabricksConfigCsv = async (file: File): Promise<ServiceResponse<{ message: string }>> => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${baseURL}/databricks/upload-config`, {
            method: 'POST',
            body: formData,
        });
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const getDatabricksCatalogs = async (): Promise<ServiceResponse<{ catalogs: any[] }>> => {
    try {
        const response = await fetch(`${baseURL}/databricks/catalogs`);
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const getDatabricksSchemas = async (catalog: string): Promise<ServiceResponse<{ schemas: any[] }>> => {
    try {
        const response = await fetch(`${baseURL}/databricks/schemas/${catalog}`);
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const getDatabricksTables = async (catalog: string, schema: string): Promise<ServiceResponse<{ tables: any[] }>> => {
    try {
        const response = await fetch(`${baseURL}/databricks/tables/${catalog}/${schema}`);
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};

export const getDatabricksTableData = async (catalog: string, schema: string, table: string): Promise<ServiceResponse<{ table_data: any }>> => {
    try {
        const response = await fetch(`${baseURL}/databricks/tables/${catalog}/${schema}/${table}/data`);
        const resData = await response.json();
        if (resData?.success) {
            return { data: resData?.data, error: null };
        } else {
            return { data: null, error: resData?.message || `HTTP ${response.status}` };
        }
    } catch (error: any) {
        return { data: null, error: error.message };
    }
};
