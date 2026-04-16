import {
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LinearScale,
    Title,
    Tooltip,
} from 'chart.js';
import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { fetchMongoDBData } from '../services/mongodb'; // Adjust path as needed

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface MongoDataViewerProps {
    databaseName: string;
    collectionName: string;
    queryFilter?: { [key: string]: any };
}

const MongoDataViewer: React.FC<MongoDataViewerProps> = ({
    databaseName,
    collectionName,
    queryFilter
}) => {
    const [data, setData] = useState<any[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const getMongoDBData = async () => {
            setLoading(true);
            setError(null);
            const config = {
                uri: import.meta.env.VITE_MONGO_URI,
                database_name: "pro-village",
                collection_name: "pro-village",
                query_filter: queryFilter,
            };
            const result = await fetchMongoDBData(config);
            if (result.error) {
                setError(result.error);
            } else {
                setData(result.data);
            }
            setLoading(false);
        };

        getMongoDBData();
    }, [databaseName, collectionName, queryFilter]); // Re-fetch if these props change

    if (loading) return <div className="text-center py-4">Loading MongoDB data...</div>;
    if (error) return <div className="text-red-500 text-center py-4">Error: {error}</div>;
    if (!data || data.length === 0) return <div className="text-center py-4">No data found.</div>;

    // --- Example Visualization with Chart.js ---
    // This example assumes your data has a 'category' and 'value' field for a bar chart.
    // You'll need to adapt this based on the actual structure of your MongoDB documents.
    const chartLabels = data.map((item: any) => item.name || item._id); // Example: use 'name' field as label
    const chartValues = data.map((item: any) => item.count || 1); // Example: use 'count' field as value

    const chartData = {
        labels: chartLabels,
        datasets: [
            {
                label: `Count of Items in ${collectionName}`,
                data: chartValues,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: `Data from ${collectionName}`,
            },
        },
    };

    return (
        <div className="p-6 bg-white rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4">MongoDB Data from '{collectionName}'</h2>
            <div className="max-h-96 overflow-y-auto mb-4">
                <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
                    {JSON.stringify(data, null, 2)}
                </pre>
            </div>

            {/* Simple Bar Chart */}
            <h3 className="text-xl font-semibold mb-3">Visualization:</h3>
            <div className="w-full h-80"> {/* Adjust height as needed */}
                <Bar data={chartData} options={chartOptions} />
            </div>

            {/* You can add more complex visualizations or tables here */}
        </div>
    );
};

export default MongoDataViewer;
