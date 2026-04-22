const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const baseURL = `${API_BASE}/api/aws`;

export interface AWSDataResponse {
    columns: string[];
    data: Record<string, any>[];
}

export interface ServiceResponse<T> {
    data: T | null;
    error: string | null;
}

export const uploadToS3 = async (file: File): Promise<ServiceResponse<{ message: string; s3_key: string }>> => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${baseURL}/upload`, {
            method: 'POST',
            body: formData,
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

export const fetchS3Data = async (s3Key: string): Promise<ServiceResponse<AWSDataResponse>> => {
    try {
        const response = await fetch(`${baseURL}/data/${encodeURIComponent(s3Key)}`);
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
