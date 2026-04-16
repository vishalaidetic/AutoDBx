import toast from 'react-hot-toast';

const BASE_URL = "http://127.0.0.1:8000";

interface ApiResponse {
    stdout: string;
    stderr: string;
    returncode: number;
    message?: string;
}

interface AutodbxFoldersResponse {
    folders: string[];
    error?: string;
}

// export const cloneRepository = async (repoUrl: string, baseDir: string, branch: string | null): Promise<ApiResponse> => {
//     try {
//         let url = `${BASE_URL}/github/clone?repo_url=${encodeURIComponent(repoUrl)}&base_dir=${encodeURIComponent(baseDir)}`;
//         if (branch) {
//             url += `&branch=${encodeURIComponent(branch)}`;
//         }

//         const response = await fetch(url, { method: 'POST' });
//         const data = await response.json();

//         if (response.ok) {
//             toast.success(data.message || 'Repository cloned successfully!');
//             return { ...data, returncode: 0 };
//         } else {
//             let errorMessage: string;
//             if (typeof data.detail === 'string') {
//                 errorMessage = data.detail;
//             } else if (Array.isArray(data.detail) && data.detail.length > 0) {
//                 errorMessage = data.detail.map((d: any) => d.msg || d).join(', ');
//             } else {
//                 errorMessage = data.message || data.stderr || 'Failed to clone repository.';
//             }
//             toast.error(errorMessage);
//             return { ...data, stderr: errorMessage, returncode: response.status };
//         }
//     } catch (error: any) {
//         toast.error(`Error cloning repository: ${error?.message || error}`);
//         return { stdout: '', stderr: error?.message || String(error), returncode: 1 };
//     }
// };

const handleStreamingResponse = async (response: Response, onChunk: (chunk: string) => void): Promise<string> => { // Changed return type to Promise<string> to return full output
    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error("Failed to get reader for streaming response.");
    }

    let fullOutput = ''; // To collect the full output
    const decoder = new TextDecoder();
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullOutput += chunk;
        onChunk(chunk);
    }

    // Check for the specific error message from the backend stream
    if (fullOutput.includes("ERROR: Command") && fullOutput.includes("failed with exit code 1 in directory")) {
        throw new Error(`Command execution failed: ${fullOutput.split("ERROR:")[1]?.trim() || "See output console for details."}`);
    }
    return fullOutput; // Return full output
};

export const databricksValidate = async (project_name: string, onChunk: (chunk: string) => void): Promise<void> => {
    try {
        const response = await fetch(`${BASE_URL}/databricks/validate?project_name=${encodeURIComponent(project_name)}`, {
            method: 'GET',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Validation failed. HTTP error.');
        }
        const output = await handleStreamingResponse(response, onChunk);
        // If handleStreamingResponse throws, this part won't be reached
        toast.success('Databricks validation completed!');
    } catch (error: any) {
        toast.error(`Databricks validation error: ${error.message}`);
        onChunk(`Error: ${error.message}\n`);
        throw error; // Re-throw to be caught by handleAction
    }
};

export const databricksDeploy = async (project_name: string, onChunk: (chunk: string) => void): Promise<void> => {
    try {
        const response = await fetch(`${BASE_URL}/databricks/deploy?project_name=${encodeURIComponent(project_name)}`, {
            method: 'GET',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Deployment failed. HTTP error.');
        }
        await handleStreamingResponse(response, onChunk);
        toast.success('Databricks deployment completed!');
    } catch (error: any) {
        toast.error(`Databricks deployment error: ${error.message}`);
        onChunk(`Error: ${error.message}\n`);
        throw error; // Re-throw to be caught by handleAction
    }
};

export const databricksRunConfigTable = async (project_name: string, onChunk: (chunk: string) => void): Promise<void> => {
    try {
        const response = await fetch(`${BASE_URL}/databricks/run/config-table?project_name=${encodeURIComponent(project_name)}`, {
            method: 'GET',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Config table creation failed. HTTP error.');
        }
        await handleStreamingResponse(response, onChunk);
        toast.success('Config table creation job started!');
    } catch (error: any) {
        toast.error(`Config table creation error: ${error.message}\n`);
        onChunk(`Error: ${error.message}\n`);
        throw error; // Re-throw to be caught by handleAction
    }
};

export const databricksRunMigrationJob = async (project_name: string, onChunk: (chunk: string) => void): Promise<void> => {
    try {
        const response = await fetch(`${BASE_URL}/databricks/run/migration-job?project_name=${encodeURIComponent(project_name)}`, {
            method: 'GET',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Migration job failed. HTTP error.');
        }
        await handleStreamingResponse(response, onChunk);
        toast.success('Migration job started!');
    } catch (error: any) {
        toast.error(`Migration job error: ${error.message}`);
        onChunk(`Error: ${error.message}\n`);
        throw error; // Re-throw to be caught by handleAction
    }
};

export const fetchAutodbxFolders = async (): Promise<AutodbxFoldersResponse> => {
    try {
        const response = await fetch(`${BASE_URL}/autodbx/folders`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch AutoDBx folders');
        }
        const result: AutodbxFoldersResponse = await response.json();
        return result;
    } catch (error: any) {
        console.error('Error fetching AutoDBx folders:', error);
        return { folders: [], error: error.message || 'An unknown error occurred' };
    }
};

export const uploadDatabricksConfigCsv = async (file: File): Promise<ApiResponse> => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${BASE_URL}/databricks/upload-config`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (response.ok) {
            toast.success(data.message || 'Databricks configuration uploaded successfully!');
            return { ...data, returncode: 0 };
        } else {
            let errorMessage: string;
            if (typeof data.detail === 'string') {
                errorMessage = data.detail;
            } else if (Array.isArray(data.detail) && data.detail.length > 0) {
                errorMessage = data.detail.map((d: any) => d.msg || d).join(', ');
            } else {
                errorMessage = data.message || data.stderr || 'Failed to upload Databricks configuration.';
            }
            toast.error(errorMessage);
            return { ...data, stderr: errorMessage, returncode: response.status };
        }
    } catch (error: any) {
        toast.error(`Error uploading Databricks configuration: ${error?.message || error}`);
        return { stdout: '', stderr: error?.message || String(error), returncode: 1 };
    }
};