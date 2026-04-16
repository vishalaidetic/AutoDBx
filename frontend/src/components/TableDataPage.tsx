import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchDatabricksTableData } from '../services/databricksService';
import { Terminal, Database, Table } from 'lucide-react';
import { useLoader } from '../services/loader';
import { toast } from 'react-hot-toast';

interface TableDataResponse {
  columns: string[];
  data: Record<string, any>[];
}

export default function TableDataPage() {
  const { catalogName, schemaName, tableName } = useParams<{ catalogName: string; schemaName: string; tableName: string }>();
  const [tableData, setTableData] = useState<TableDataResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const { show, hide } = useLoader();

  useEffect(() => {
    let isMounted = true;
    async function getTableData() {
      show('Loading table data...');
      setLoading(true);
      setError(null);
      setTableData(null);

      if (!catalogName || !schemaName || !tableName) {
        setError('Missing catalog, schema, or table name in URL parameters.');
        setLoading(false);
        hide();
        return;
      }

      try {
        const fetchedData = await fetchDatabricksTableData(
          decodeURIComponent(catalogName),
          decodeURIComponent(schemaName),
          decodeURIComponent(tableName)
        );
        if (isMounted) {
          setTableData(fetchedData);
          toast.success(`Data loaded for table: ${decodeURIComponent(tableName)}`);
        }
      } catch (err: any) {
        if (isMounted) {
          const errorMessage = err?.message || `Failed to fetch data for table ${decodeURIComponent(tableName)}`;
          setError(errorMessage);
          toast.error(errorMessage);
        }
      } finally {
        if (isMounted) setLoading(false);
        hide();
      }
    }

    getTableData();

    return () => {
      isMounted = false;
    };
  }, [catalogName, schemaName, tableName, show, hide]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 flex items-center justify-center p-8 transition-all duration-300 ease-in-out">
        <div className="max-w-7xl w-full bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg flex items-center justify-center min-h-[250px] transition-all duration-300 ease-in-out">
          <div className="flex flex-col items-center gap-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
            <div className="text-xl font-semibold text-gray-800">
              Fetching data for table <span className="text-blue-600">{decodeURIComponent(tableName || '')}</span>...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 flex items-center justify-center p-8 transition-all duration-300 ease-in-out">
        <div className="max-w-7xl w-full bg-red-50 border border-red-200 rounded-2xl p-6 shadow-lg transition-all duration-300 ease-in-out">
          <div className="flex items-start space-x-3">
            <Terminal className="h-6 w-6 text-red-500 mt-1" />
            <div>
              <div className="font-semibold text-red-700 text-lg">Error loading data</div>
              <div className="text-red-600 text-base">{error}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!tableData || tableData.data.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 flex items-center justify-center p-8 transition-all duration-300 ease-in-out">
        <div className="max-w-7xl w-full bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg text-center transition-all duration-300 ease-in-out">
          <Database className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No data found</h3>
          <p className="text-gray-600">No data available for table <span className="font-bold">{decodeURIComponent(tableName || '')}</span>.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 py-12 transition-all duration-300 ease-in-out">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-300 ease-in-out">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg hover:border-gray-300/50 hover:shadow-xl transition-all duration-300 ease-in-out">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Table className="h-6 w-6 mr-3 text-blue-600" />
            Data for Table: <span className="text-blue-600 ml-2">{decodeURIComponent(tableName || '')}</span>
          </h2>
          <div className="overflow-x-auto rounded-lg border border-gray-200 transition-all duration-300 ease-in-out">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {tableData.columns.map((colName: string) => (
                    <th key={colName} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {colName}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tableData.data.map((row: Record<string, any>, rowIndex: number) => (
                  <tr key={rowIndex} className="hover:bg-gray-50 transition-colors duration-150">
                    {tableData.columns.map((colName: string) => (
                      <td key={`${rowIndex}-${colName}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {row[colName] !== undefined && row[colName] !== null
                          ? String(row[colName])
                          : 'N/A'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
