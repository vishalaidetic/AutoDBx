export type PageType = 'upload' | 'preview' | 'execution';

export interface CsvData {
    columns: string[];
    rows: Record<string, string>[];
}

export type StageStatus = 'pending' | 'loading' | 'running' | 'success' | 'failure' | 'failed';

export interface Stage {
    id: string;
    name: string;
    status: StageStatus;
    output: string;
    errorInfo: string;
}

export interface AppState {
    currentPage: PageType;
    dataCsv: File | null;
    credentialsCsv: File | null;
    parsedData: CsvData | null;
    parsedCredentials: CsvData | null;
    source: string;
    destination: string;
    selectedFolder: string;
}
