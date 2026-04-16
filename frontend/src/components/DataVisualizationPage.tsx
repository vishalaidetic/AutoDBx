import { useState, useMemo, useRef, useEffect, useCallback } from 'react'; // Added useCallback
import { ChevronDown, Database, RefreshCw, LayoutList, LayoutGrid, ArrowDown } from 'lucide-react';
import { fetchDatabricksCatalogs, fetchDatabricksSchemasForCatalog } from '../services/databricksService';
import { Catalog } from '../services/modal';
import TablesFromSchema from './TablesFromSchema';
import ViewTable from './ViewTable';
import { useLoader } from '../services/loader';
import { toast } from 'react-hot-toast';
import MongoDataViewer from './MongoDataViewer'; // Adjust path


// Define Schema type for TypeScript
type Schema = {
  name: string;
  catalog_name: string; // Add catalog_name to Schema type
  // Add other properties as needed
};

export default function DataVisualizationPage() {
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const [visualizationMode, setVisualizationMode] = useState<'card' | 'table'>('card');

  // Databricks Catalogs state
  const [databricksCatalogs, setDatabricksCatalogs] = useState<Catalog[]>([]);
  const [loadingDatabricksCatalogs, setLoadingDatabricksCatalogs] = useState<boolean>(true);
  const [errorDatabricksCatalogs, setErrorDatabricksCatalogs] = useState<string | null>(null);

  // Schemas for selected catalog
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [loadingSchemas, setLoadingSchemas] = useState<boolean>(false);
  const [errorSchemas, setErrorSchemas] = useState<string | null>(null);
  const [selectedSchemaName, setSelectedSchemaName] = useState<string | null>(null); // State for selected schema

  // States for selected table details and parallel view
  const [selectedTableCatalogName, setSelectedTableCatalogName] = useState<string | null>(null);
  const [selectedTableSchemaName, setSelectedTableSchemaName] = useState<string | null>(null);
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [showParallelView, setShowParallelView] = useState<boolean>(false); // New state for parallel view
  const [showScrollHint, setShowScrollHint] = useState<boolean>(false); // New state for scroll hint visibility

  // Pagination for schemas
  const [displayedCount, setDisplayedCount] = useState<number>(10);

  // Dropdown ref for click outside
  const dropdownRef = useRef<HTMLDivElement>(null);
  const tablesContainerRef = useRef<HTMLDivElement>(null); // Ref for the TablesFromSchema container

  const { show, hide } = useLoader(); // Initialize useLoader hook

  // Handle click outside dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    }
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Fetch Databricks Catalogs on mount
  useEffect(() => {
    async function getDatabricksCatalogs() {
      try {
        show('Fetching Databricks catalogs...'); // Show loader with message
        setLoadingDatabricksCatalogs(true);
        const fetchedCatalogs = await fetchDatabricksCatalogs();
        setDatabricksCatalogs(fetchedCatalogs);
        setErrorDatabricksCatalogs(null);
      } catch (err: any) {
        const errorMessage = err?.message || 'Failed to fetch Databricks catalogs';
        setErrorDatabricksCatalogs(errorMessage);
        toast.error(errorMessage); // Show error toast
      } finally {
        setLoadingDatabricksCatalogs(false);
        hide(); // Hide loader
      }
    }
    getDatabricksCatalogs();
  }, [show, hide]);

  // Combine Databricks catalogs
  const allDataProviders = useMemo(() => {
    // Map Databricks catalogs
    const dbCatalogs = databricksCatalogs.map(c => ({
      id: `databricks-${c.name}`, // Prefix to avoid ID collisions
      name: c.full_name,
      description: c.catalog_type,
      color: 'bg-indigo-500', // Assign a distinct color for Databricks catalogs
      type: 'databricks',
      originalId: c.name, // Store original name for API calls
    }));
    return [...dbCatalogs];
  }, [databricksCatalogs]);

  // Fetch schemas for selected provider when it changes
  useEffect(() => {
    async function fetchSchemasForProvider() {
      if (!selectedProvider) {
        setSchemas([]);
        setErrorSchemas(null);
        setLoadingSchemas(false);
        setDisplayedCount(10);
        setSelectedSchemaName(null); // Clear selected schema when catalog changes
        setSelectedTableName(null); // Clear selected table when catalog changes
        setSelectedTableSchemaName(null);
        setSelectedTableCatalogName(null);
        setShowParallelView(false); // Reset parallel view
        setShowScrollHint(false); // Hide arrow if no provider is selected
        return;
      }
      setLoadingSchemas(true);
      setErrorSchemas(null);
      setSchemas([]);
      setDisplayedCount(10);
      setSelectedSchemaName(null); // Clear selected schema when catalog changes
      setSelectedTableName(null); // Clear selected table when catalog changes
      setSelectedTableSchemaName(null);
      setSelectedTableCatalogName(null);
      setShowParallelView(false); // Reset parallel view
      setShowScrollHint(false); // Hide arrow while loading new schemas
      // Find the provider info
      const provider = allDataProviders.find(p => p.id === selectedProvider);
      if (!provider) {
        setErrorSchemas('Invalid provider selected');
        setLoadingSchemas(false);
        return;
      }
      try {
        show(`Fetching schemas for ${provider.name}...`); // Show loader with message
        // Call the function to fetch schemas for the selected catalog
        const fetchedSchemas = await fetchDatabricksSchemasForCatalog(provider.originalId);
        setSchemas(fetchedSchemas);
        setErrorSchemas(null);
        toast.success(`Loaded ${fetchedSchemas.length} schemas for ${provider.name}`); // Success toast
        if (fetchedSchemas.length > 0) { // Show arrow if schemas are loaded
            setShowScrollHint(true);
        }
      } catch (err: any) {
        const errorMessage = err?.message || 'Failed to fetch schemas';
        setErrorSchemas(errorMessage);
        toast.error(errorMessage); // Show error toast
      } finally {
        setLoadingSchemas(false);
        hide(); // Hide loader
      }
    }
    fetchSchemasForProvider();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProvider, allDataProviders, show, hide]); // Add show, hide to dependency array

  // Handle scroll to hide the arrow
  const handleScroll = useCallback(() => {
    if (tablesContainerRef.current && showScrollHint) {
      const rect = tablesContainerRef.current.getBoundingClientRect();
      // Hide if the top of the tables container is well within the viewport
      if (rect.top < window.innerHeight * 0.75) { // Adjust threshold as needed
        setShowScrollHint(false);
      }
    }
  }, [showScrollHint]);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);


  // Pagination logic for schemas
  const displayedSchemas = useMemo(() => {
    return schemas.slice(0, displayedCount);
  }, [schemas, displayedCount]);

  const hasMoreSchemas = displayedCount < schemas.length;

  const handleLoadMore = () => {
    setDisplayedCount(prev => Math.min(prev + 10, schemas.length));
  };

  const selectedProviderInfo = useMemo(() => {
    return allDataProviders.find(p => p.id === selectedProvider);
  }, [selectedProvider, allDataProviders]);

  const handleSchemaClick = (schemaName: string) => {
    setSelectedSchemaName(schemaName);
    setSelectedTableName(null); // Clear selected table when a new schema is clicked
    setSelectedTableSchemaName(null);
    setSelectedTableCatalogName(null);
    setShowParallelView(false); // Reset parallel view
    setShowScrollHint(true); // Show arrow again when a new schema is clicked
  };

  const handleTableClick = (catalogName: string, schemaName: string, tableName: string) => {
    setSelectedTableCatalogName(catalogName);
    setSelectedTableSchemaName(schemaName);
    setSelectedTableName(tableName);
    setShowParallelView(true); // Activate parallel view when a table is selected
    setShowScrollHint(false); // Hide arrow when a table is selected for parallel view
  };

  // Function to open table data in a new browser window
  const handleOpenTableDataInNewPage = (catalogName: string, schemaName: string, tableName: string) => {
    const path = `/data-view/${encodeURIComponent(catalogName)}/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}`;
    const url = `${window.location.origin}${path}`;
    window.open(url, '_blank', 'noopener,noreferrer'); // Removed width and height
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 py-12 transition-all duration-300 ease-in-out">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-300 ease-in-out">
        {/* Header */}
        <div className="text-center mb-12 transition-all duration-300 ease-in-out">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Databricks <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Visualization</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Select a Catalog to explore and visualize your data.
          </p>
        </div>

        <div className={`grid gap-8 transition-all duration-500 ease-in-out ${showParallelView ? 'md:grid-cols-2' : 'grid-cols-1'}`}>
          {/* Left Column: Catalog and Schema Selection and TablesFromSchema */}
          <div className={`${showParallelView ? 'col-span-1' : 'col-span-full'}`}>
            {/* Provider Selection (Databricks Catalog) */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 mb-8 relative z-30 shadow-lg hover:border-gray-300/50 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-gray-800 flex items-center">
                  <Database className="h-6 w-6 mr-3 text-blue-600" />
                  Select Catalog
                </h2>
                {selectedProvider && (
                  <div className="flex items-center text-sm text-gray-500">
                    <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                    {schemas.length} schemas available
                  </div>
                )}
              </div>

              {/* Dropdown for Catalogs */}
              <div className="relative w-full" ref={dropdownRef}>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="group w-full flex items-center justify-between px-6 py-3 text-left bg-white border border-gray-300 rounded-xl hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 shadow-sm"
                  aria-haspopup="listbox"
                  aria-expanded={isDropdownOpen}
                  type="button"
                  disabled={loadingDatabricksCatalogs}
                >
                  {selectedProvider ? (
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-3 ${selectedProviderInfo?.color}`} />
                      <div>
                        <div className="font-medium text-gray-900">{selectedProviderInfo?.name}</div>
                        <div className="text-sm text-gray-500">{selectedProviderInfo?.description}</div>
                      </div>
                    </div>
                  ) : (
                    <span className="text-gray-500">Select a Catalog...</span>
                  )}
                  <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform group-hover:rotate-180 ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {isDropdownOpen && (
                  <div
                    className="absolute left-0 top-full z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
                    role="listbox"
                  >
                    {loadingDatabricksCatalogs && (
                      <div className="px-4 py-3 text-gray-500 text-sm">Loading Databricks catalogs...</div>
                    )}
                    {errorDatabricksCatalogs && (
                      <div className="px-4 py-3 text-red-500 text-sm">{errorDatabricksCatalogs}</div>
                    )}
                    {allDataProviders.map((provider) => (
                      <button
                        key={provider.id}
                        onClick={() => {
                          setSelectedProvider(provider.id);
                          setIsDropdownOpen(false);
                        }}
                        className="w-full flex items-center px-4 py-3 text-left hover:bg-gray-50 transition-colors duration-200"
                        role="option"
                        aria-selected={selectedProvider === provider.id}
                      >
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${provider.color}`} />
                          <div>
                            <div className="font-medium text-gray-900">{provider.name}</div>
                            <div className="text-sm text-gray-500">{provider.description}</div>
                          </div>
                        </div>
                      </button>
                    ))}
                    {allDataProviders.length === 0 && !loadingDatabricksCatalogs && !errorDatabricksCatalogs && (
                      <div className="px-4 py-3 text-gray-500 text-sm">No Catalogs available</div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Data Display (Schemas) */}
            {selectedProvider && (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 relative z-10 shadow-lg hover:border-gray-300/50 hover:shadow-xl transition-all duration-300">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">Schemas</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setVisualizationMode('card')}
                      className={`group inline-flex items-center px-4 py-2 rounded-xl text-sm font-medium transition-colors duration-200 ${
                        visualizationMode === 'card'
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      <LayoutGrid className="h-4 w-4 mr-2" />
                      Card View
                    </button>
                    <button
                      onClick={() => setVisualizationMode('table')}
                      className={`group inline-flex items-center px-4 py-2 rounded-xl text-sm font-medium transition-colors duration-200 ${
                        visualizationMode === 'table'
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      <LayoutList className="h-4 w-4 mr-2" />
                      Table View
                    </button>
                  </div>
                </div>

                {loadingSchemas ? (
                  <div className="text-center text-gray-500 py-8">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 mx-auto mb-4" />
                    Loading schemas...
                  </div>
                ) : errorSchemas ? (
                  <div className="w-full bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                    <svg className="h-5 w-5 text-red-500 mt-1" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12A9 9 0 1 1 3 12a9 9 0 0 1 18 0Z" />
                    </svg>
                    <div>
                      <div className="font-semibold text-red-700">Error</div>
                      <div className="text-red-600">{errorSchemas}</div>
                    </div>
                  </div>
                ) : (
                  <div className="transition-opacity duration-500 ease-in-out"> {/* Added transition here */}
                    {visualizationMode === 'card' ? (
                      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {displayedSchemas.map((schema) => (
                          <div
                            key={schema.name}
                            onClick={() => handleSchemaClick(schema.name)}
                            className={`group bg-white border border-gray-200 rounded-xl p-5 hover:border-gray-300 hover:shadow-md transition-all duration-200 hover:-translate-y-1 cursor-pointer ${
                              selectedSchemaName === schema.name ? 'ring-2 ring-blue-500' : ''
                            }`}
                          >
                            <div className="flex items-start justify-between mb-3">
                              <h4 className="font-semibold text-gray-900 truncate">{schema.name}</h4>
                            </div>
                          </div>
                        ))}
                        {displayedSchemas.length === 0 && (
                          <div className="col-span-full text-center text-gray-500 py-8">
                            No schemas available for this catalog.
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 rounded-lg border border-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Name
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {displayedSchemas.map((schema) => (
                              <tr
                                key={schema.name}
                                onClick={() => handleSchemaClick(schema.name)}
                                className={`cursor-pointer hover:bg-gray-50 ${
                                  selectedSchemaName === schema.name ? 'bg-blue-50' : ''
                                }`}
                              >
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{schema.name}</td>
                              </tr>
                            ))}
                            {displayedSchemas.length === 0 && (
                              <tr>
                                <td colSpan={1} className="text-center text-gray-500 py-8">
                                  No schemas available for this catalog.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {hasMoreSchemas && !loadingSchemas && !errorSchemas && (
                      <div className="text-center mt-8 transition-opacity duration-300 ease-in-out">
                        <button
                          onClick={handleLoadMore}
                          className="group inline-flex items-center justify-center px-6 py-3 text-base font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl hover:from-blue-700 hover:to-purple-700 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
                        >
                          Load More Schemas
                          <ChevronDown className="ml-2 h-5 w-5 group-hover:translate-y-1 transition-transform" />
                        </button>
                      </div>
                    )}

                    {!hasMoreSchemas && displayedSchemas.length > 0 && !loadingSchemas && !errorSchemas && (
                      <div className="text-center mt-8 transition-opacity duration-300 ease-in-out">
                        <p className="text-gray-500">All schemas have been loaded</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Visual cue: Arrow pointing down to tables */}
            {selectedProvider && selectedSchemaName && !loadingSchemas && !selectedTableName && showScrollHint && (
                <div className="text-center mt-8 animate-bounce transition-opacity duration-500 ease-in-out">
                    <ArrowDown className="h-10 w-10 text-blue-500 mx-auto" />
                    <p className="text-gray-600 text-sm mt-2">Scroll down to see tables</p>
                </div>
            )}

            {/* TablesFromSchema renders here, below the schemas section */}
            {selectedSchemaName && selectedProviderInfo && !selectedTableName && (
              <div ref={tablesContainerRef} className={`mt-8 ${showParallelView ? 'col-span-1' : 'col-span-full'}`}>
                <TablesFromSchema
                  catalogName={selectedProviderInfo.originalId}
                  schemaName={selectedSchemaName}
                  onTableClick={handleTableClick}
                />
              </div>
            )}
          </div>

          {/* Right Column: Tables and Table Details/Data */}
          {selectedProvider && (selectedSchemaName || selectedTableName) && showParallelView && ( // Only show right column if parallel view is active
            <div className={`col-span-1 ${showParallelView ? '' : 'mt-8'}`}>
              {selectedTableCatalogName && selectedTableSchemaName && selectedTableName && (
                <ViewTable
                  catalogName={selectedTableCatalogName}
                  schemaName={selectedTableSchemaName}
                  tableName={selectedTableName}
                  onOpenTableDataInNewPage={handleOpenTableDataInNewPage}
                />
              )}
            </div>
          )}
        </div>

        {!selectedProvider && (
          <div className="text-center py-16 bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-lg transition-all duration-300 ease-in-out">
            <Database className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Select a Catalog</h3>
            <p className="text-gray-600 max-w-sm mx-auto">Choose a data source from the dropdown above to start exploring your data.</p>
          </div>
        )}
      </div>

      {/* MongoDB Data Viewer */}
      <MongoDataViewer 
        databaseName="pro_village" 
        collectionName="users" 
        // queryFilter={{ age: { $gt: 25 } }} // Example filter
      />
    </div>
  );
}