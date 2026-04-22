import { ChevronDown, Table2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-hot-toast';
import { fetchDatabricksTablesForSchema } from '../services/databricksService';
import { useLoader } from '../services/loader';
import { DatabricksTable } from '../services/modal';

interface TablesFromSchemaProps {
  catalogName: string;
  schemaName: string;
  onTableClick: (catalogName: string, schemaName: string, tableName: string) => void;
}

const formatIndianDateTime = (timestamp: number | undefined): string => {
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp);
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
};

export default function TablesFromSchema({ catalogName, schemaName, onTableClick }: TablesFromSchemaProps) {
  const [tables, setTables] = useState<DatabricksTable[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [displayedCount, setDisplayedCount] = useState<number>(10);

  const { show, hide } = useLoader();

  useEffect(() => {
    let isMounted = true;
    async function getTables() {
      show(`Fetching tables for ${schemaName}...`);
      setLoading(true);
      setError(null);
      setTables([]);
      setDisplayedCount(10);
      try {
        const { data: fetchedTables, error: fetchError } = await fetchDatabricksTablesForSchema(catalogName, schemaName);
        if (isMounted) {
          if (fetchedTables) {
            setTables(Array.isArray(fetchedTables) ? fetchedTables : []);
            toast.success(`Loaded ${fetchedTables.length} tables for ${schemaName}`);
          } else {
            setError(fetchError || 'Failed to fetch tables');
            setTables([]);
            toast.error(fetchError || 'Failed to fetch tables');
          }
        }
      } catch (err: any) {
        if (isMounted) {
          const errorMessage = err?.message || 'Failed to fetch tables';
          setError(errorMessage);
          setTables([]);
          toast.error(errorMessage);
        }
      } finally {
        if (isMounted) setLoading(false);
        hide();
      }
    }

    if (catalogName && schemaName) {
      getTables();
    } else {
      setTables([]);
      setLoading(false);
      hide();
    }

    return () => {
      isMounted = false;
    };
  }, [catalogName, schemaName, show, hide]);

  const safeTables: DatabricksTable[] = useMemo(() => Array.isArray(tables) ? tables : [], [tables]);
  const displayedTables = useMemo(() => safeTables.slice(0, displayedCount), [safeTables, displayedCount]);
  const hasMoreTables = displayedCount < safeTables.length;

  const handleLoadMore = () => {
    setDisplayedCount(prev => Math.min(prev + 10, safeTables.length));
  };

  if (loading) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg flex items-center justify-center min-h-[200px] transition-all duration-300 ease-in-out">
        <div className="flex items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          <div className="text-md font-semibold text-gray-800">
            Fetching tables for <span className="text-blue-600">{schemaName}</span>...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 shadow-lg transition-all duration-300 ease-in-out">
        <div className="flex items-start space-x-3">
          <svg className="h-6 w-6 text-red-500 mt-1" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12A9 9 0 1 1 3 12a9 9 0 0 1 18 0Z" />
          </svg>
          <div>
            <div className="font-semibold text-red-700">Error loading tables</div>
            <div className="text-red-600">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg hover:border-gray-300/50 hover:shadow-xl transition-all duration-300 ease-in-out">
      <div className="flex items-center justify-between border-b border-gray-200 pb-6 mb-6 transition-all duration-300 ease-in-out">
        <h2 className="text-2xl font-semibold text-gray-800 flex items-center">
          <Table2 className="h-6 w-6 mr-3 text-gray-600" />
          Tables in <span className="font-bold text-blue-600 ml-2">{schemaName}</span>
        </h2>
        {safeTables.length > 0 && (
          <span className="text-sm text-gray-500 transition-opacity duration-300 ease-in-out">({displayedTables.length} of {safeTables.length})</span>
        )}
      </div>
      <div>
        {safeTables.length === 0 ? (
          <p className="text-gray-500 text-center py-4 transition-opacity duration-300 ease-in-out">No tables found in this schema.</p>
        ) : (
          <div className="overflow-x-auto max-h-[400px] overflow-y-auto"> {/* Added max-h and overflow-y-auto */}
            <table className="min-w-full divide-y divide-gray-200 rounded-lg border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated At</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayedTables.map((table) => (
                  <tr
                    key={table?.full_name || table?.name}
                    className="hover:bg-gray-50 cursor-pointer transition-colors duration-150"
                    onClick={() => onTableClick(catalogName, schemaName, table.name)}
                  >
                    <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">{table?.name}</td>
                    <td className="px-6 py-4 text-gray-700 whitespace-nowrap">{table?.table_type}</td>
                    <td className="px-6 py-4 text-gray-700 whitespace-nowrap">{table?.owner}</td>
                    <td className="px-6 py-4 text-gray-700 whitespace-nowrap">{formatIndianDateTime(table?.created_at)}</td>
                    <td className="px-6 py-4 text-gray-700 whitespace-nowrap">{formatIndianDateTime(table?.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {hasMoreTables && !loading && !error && (
          <div className="text-center mt-8 transition-opacity duration-300 ease-in-out">
            <button
              onClick={handleLoadMore}
              className="group inline-flex items-center justify-center px-6 py-3 text-base font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl hover:from-blue-700 hover:to-purple-700 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
            >
              Load More Tables
              <ChevronDown className="ml-2 h-5 w-5 group-hover:translate-y-1 transition-transform" />
            </button>
          </div>
        )}

        {!hasMoreTables && safeTables.length > 0 && !loading && !error && (
          <div className="text-center mt-6 transition-opacity duration-300 ease-in-out">
            <p className="text-gray-500">All tables have been loaded</p>
          </div>
        )}
      </div>
    </div>
  );
}