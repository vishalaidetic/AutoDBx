import { Info, LayoutList, Table } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import { fetchDatabricksTableDetails } from '../services/databricksService';
import { useLoader } from '../services/loader';
import { DatabricksTableDetails, DatabricksTableDetailsColumn } from '../services/modal';

interface ViewTableProps {
  catalogName: string;
  schemaName: string;
  tableName: string;
  onOpenTableDataInNewPage: (catalogName: string, schemaName: string, tableName: string) => void;
  hideColumnsSection?: boolean;
}

export default function ViewTable({
  catalogName,
  schemaName,
  tableName,
  onOpenTableDataInNewPage,
  hideColumnsSection = false,
}: ViewTableProps) {
  const [tableDetails, setTableDetails] = useState<DatabricksTableDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const { show, hide } = useLoader();

  useEffect(() => {
    let isMounted = true;
    async function getTableDetails() {
      show('Fetching table details...');
      setLoading(true);
      setError(null);
      setTableDetails(null);

      try {
        const { data: fetchedDetails, error: fetchError } = await fetchDatabricksTableDetails(
          catalogName,
          schemaName,
          tableName
        );
        if (isMounted) {
          if (fetchedDetails) {
            setTableDetails(fetchedDetails);
            toast.success(`Details loaded for table: ${tableName}`);
          } else {
            setError(fetchError || 'Failed to fetch table details');
            toast.error(fetchError || 'Failed to fetch table details');
          }
        }
      } catch (err: any) {
        if (isMounted) {
          const errorMessage = err?.message || `Failed to fetch details for table ${tableName}`;
          setError(errorMessage);
          toast.error(errorMessage);
        }
      } finally {
        if (isMounted) setLoading(false);
        hide();
      }
    }

    if (catalogName && schemaName && tableName) {
      getTableDetails();
    } else {
      setLoading(false);
      setTableDetails(null);
    }

    return () => {
      isMounted = false;
    };
  }, [catalogName, schemaName, tableName, show, hide]);

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

  if (loading) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg flex items-center justify-center min-h-[200px] transition-all duration-300 ease-in-out">
        <div className="flex items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          <div className="text-md font-semibold text-gray-800">
            Fetching details for table <span className="text-blue-600">{tableName}</span>...
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
            <div className="font-semibold text-red-700">Error loading table details</div>
            <div className="text-red-600">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!tableDetails) {
    return (
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg transition-all duration-300 ease-in-out">
        <p className="text-gray-500 text-center py-4">No details found for table {tableName}.</p>
      </div>
    );
  }

  const { columns, owner, table_type, created_at, updated_at, full_name } = tableDetails;

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg hover:border-gray-300/50 hover:shadow-xl transition-all duration-300 ease-in-out">
      <div className="flex items-center justify-between border-b border-gray-200 pb-6 mb-6 transition-all duration-300 ease-in-out">
        <h2 className="text-2xl font-semibold text-gray-800 flex items-center">
          <Info className="h-6 w-6 mr-3 text-gray-600" />
          Table: <span className="font-bold text-blue-600 ml-2">{tableName}</span>
        </h2>
        <button
          onClick={() => onOpenTableDataInNewPage(catalogName, schemaName, tableName)}
          className="group inline-flex items-center justify-center px-6 py-3 text-base font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <Table className="mr-2 h-5 w-5 group-hover:scale-110 transition-transform" />
          View Table Data
        </button>
      </div>
      <div className="grid grid-cols-1 gap-4 text-gray-700 mb-8 transition-all duration-300 ease-in-out">
        <p>
          <strong>Full Name:</strong> {full_name || 'N/A'}
        </p>
        <p>
          <strong>Owner:</strong> {owner || 'N/A'}
        </p>
        <p>
          <strong>Table Type:</strong> {table_type || 'N/A'}
        </p>
        <p>
          <strong>Created At:</strong> {formatIndianDateTime(created_at)}
        </p>
        <p>
          <strong>Updated At:</strong> {formatIndianDateTime(updated_at)}
        </p>
      </div>

      {!hideColumnsSection && (
        <div className="mt-8 transition-all duration-300 ease-in-out">
          <h3 className="text-xl font-semibold text-gray-800 flex items-center mb-4">
            <LayoutList className="h-5 w-5 mr-2 text-gray-600" />
            Columns
          </h3>

          {columns && columns.length > 0 ? (
            <div className="overflow-x-auto max-h-[250px] overflow-y-auto rounded-lg border border-gray-200"> {/* Added max-h and overflow-y-auto */}
              <table className="min-w-full divide-y divide-gray-200 rounded-lg border border-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nullable</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comment</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {columns.map((column: DatabricksTableDetailsColumn, index: number) => (
                    <tr key={column.name || index} className="hover:bg-gray-50 transition-colors duration-150">
                      <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">
                        {column.name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-gray-700 whitespace-nowrap">
                        {column.type_text || column.type_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-gray-700 whitespace-nowrap">
                        {column.nullable ? 'Yes' : 'No'}
                      </td>
                      <td className="px-6 py-4 text-gray-700 whitespace-nowrap">
                        {column.comment || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 py-4 text-center transition-opacity duration-300 ease-in-out">No columns found for this table.</p>
          )}
        </div>
      )}
    </div>
  );
}
