// frontend/src/services/dataService.ts

interface MongoConfig {
    uri?: string;
    database_name: string;
    collection_name: string;
    query_filter?: { [key: string]: any };
}

interface MongoDataResponse {
    data: any[];
    error?: string;
}

export const fetchMongoDBData = async (config: MongoConfig): Promise<MongoDataResponse> => {
    try {
        const response = await fetch('http://127.0.0.1:8000/data/mongodb', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch MongoDB data');
        }

        const result: MongoDataResponse = await response.json();
        return result;
    } catch (error: any) {
        console.error('Error fetching MongoDB data:', error);
        return { data: [], error: error.message || 'An unknown error occurred' };
    }
};