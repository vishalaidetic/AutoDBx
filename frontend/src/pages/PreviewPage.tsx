import { ArrowRight, CheckCircle2, ChevronLeft, Database, FileText } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ToastContainer, ToastMessage, createToastId } from '../components/Toast';
import { CsvData } from '../types';

interface PreviewPageProps {
    parsedData: CsvData;
    parsedCredentials: CsvData;
    dataCsvName: string;
    onProceed: (source: string, destination: string) => void;
    onCancel: () => void;
}

export default function PreviewPage({
    parsedData,
    parsedCredentials,
    dataCsvName,
    onProceed,
    onCancel,
}: PreviewPageProps) {
    const [source, setSource] = useState('');
    const [destination, setDestination] = useState('');
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    useEffect(() => {
        // Auto-extract source from migration CSV
        if (parsedData.rows.length > 0) {
            const firstRow = parsedData.rows[0];
            // Prioritize SOURCE or SOURCE_DATABASE as seen in user's config.csv
            const foundSource = firstRow['SOURCE'] || firstRow['source'] || firstRow['SOURCE_DATABASE'] || firstRow['source_database'] || firstRow['schema'] || firstRow['SOURCE_SCHEMA'] || '';
            setSource(foundSource);
        }

        // Auto-extract destination
        let foundDestination = '';
        // First try to find it in the migration Data CSV (TARGET_TABLE_CATALOG.TARGET_TABLE_SCHEMA)
        if (parsedData.rows.length > 0) {
            const firstRow = parsedData.rows[0];
            const targetCatalog = firstRow['TARGET_TABLE_CATALOG'] || firstRow['target_catalog'] || firstRow['target_table_catalog'];
            const targetSchema = firstRow['TARGET_TABLE_SCHEMA'] || firstRow['target_schema'] || firstRow['target_table_schema'];

            if (targetCatalog && targetSchema) {
                foundDestination = `${targetCatalog}.${targetSchema}`;
            }
        }

        // Fallback: Auto-extract destination from credentials CSV if not found in migration data
        if (!foundDestination && parsedCredentials && parsedCredentials.rows.length > 0) {
            const creds = parsedCredentials.rows;
            const catalogRow = creds.find(r => {
                const param = r['parameter']?.toLowerCase() || '';
                return param === 'catalog' || param === 'target_catalog' || param === 'workspace_catalog';
            });
            const schemaRow = creds.find(r => {
                const param = r['parameter']?.toLowerCase() || '';
                return param === 'schema' || param === 'target_schema' || param === 'workspace_schema';
            });

            if (catalogRow && schemaRow) {
                foundDestination = `${catalogRow.value}.${schemaRow.value}`;
            } else if (catalogRow) {
                foundDestination = catalogRow.value;
            } else if (schemaRow) {
                foundDestination = schemaRow.value;
            }
        }
        setDestination(foundDestination || 'Databricks');
    }, [parsedData, parsedCredentials]);

    const addToast = (type: 'success' | 'error', message: string) => {
        setToasts((prev) => [...prev, { id: createToastId(), type, message }]);
    };
    const dismissToast = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

    const handleProceed = () => {
        if (!source.trim()) {
            addToast('error', 'Please ensure a source is identified.');
            return;
        }
        if (!destination.trim()) {
            addToast('error', 'Please ensure a destination is identified.');
            return;
        }
        onProceed(source.trim(), destination.trim());
    };

    return (
        <div className="flex-1 bg-slate-50 py-8">
            <div className="w-full px-6">
                <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-600 to-blue-800 p-8 text-white">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                                <Database className="w-7 h-7" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold">Dataset Preview</h1>
                                <p className="opacity-80 text-sm mt-0.5">
                                    Review your migration data and identified configuration.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="p-8">
                        <div className="space-y-8">
                            {/* Migration Configuration Section */}
                            <div className="bg-slate-50/50 rounded-2xl p-6 border border-slate-200">
                                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6">
                                    Migration Configuration
                                </h4>
                                <div className="flex flex-col md:flex-row items-center gap-6">
                                    {/* Source Box */}
                                    <div className="flex-1 w-full bg-white border border-slate-200 rounded-xl p-5 shadow-sm relative group hover:border-blue-400 transition-all duration-300">
                                        <div className="absolute top-3 right-3">
                                            <CheckCircle2 className="w-5 h-5 text-blue-500" />
                                        </div>
                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 block text-center">Source</span>
                                        <div className="text-center">
                                            <div className="text-lg font-bold text-slate-800 break-all">{source || 'Not Found'}</div>
                                        </div>
                                    </div>

                                    {/* Connector */}
                                    <div className="hidden md:flex items-center justify-center p-3 bg-blue-50 rounded-full">
                                        <ArrowRight className="w-6 h-6 text-blue-500" />
                                    </div>

                                    {/* Destination Box */}
                                    <div className="flex-1 w-full bg-white border border-slate-300 rounded-xl p-5 shadow-sm relative group hover:border-blue-400 transition-all duration-300">
                                        <div className="absolute top-3 right-3">
                                            <CheckCircle2 className="w-5 h-5 text-blue-500" />
                                        </div>
                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 block text-center">Destination</span>
                                        <div className="text-center">
                                            <div className="text-lg font-bold text-slate-800 break-all text-blue-600">{destination}</div>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-3 w-full md:w-auto">
                                        <button
                                            onClick={onCancel}
                                            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl border border-slate-200 text-slate-600 font-semibold text-sm hover:bg-white hover:border-slate-300 transition-all"
                                        >
                                            <ChevronLeft className="w-4 h-4" />
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleProceed}
                                            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-blue-600 text-white font-bold text-sm hover:bg-blue-700 hover:shadow-lg transform active:scale-95 transition-all"
                                        >
                                            Proceed
                                            <ArrowRight className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Data Table Section */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                                        <FileText className="w-5 h-5 text-blue-600" />
                                        {dataCsvName}
                                    </h3>
                                    <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-bold border border-blue-100">
                                        {parsedData.rows.length} {parsedData.rows.length === 1 ? 'Row' : 'Rows'} Loaded
                                    </span>
                                </div>

                                {parsedData.rows.length > 0 ? (
                                    <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm bg-slate-50/30">
                                        <table className="min-w-full divide-y divide-slate-200">
                                            <thead className="bg-slate-50/80">
                                                <tr>
                                                    <th className="px-5 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider w-12 text-center">
                                                        #
                                                    </th>
                                                    {parsedData.columns.map((col) => (
                                                        <th
                                                            key={col}
                                                            className="px-5 py-4 text-left text-[10px] font-bold text-slate-500 uppercase tracking-wider"
                                                        >
                                                            {col}
                                                        </th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-slate-100">
                                                {parsedData.rows.map((row, i) => (
                                                    <tr
                                                        key={i}
                                                        className={`transition-colors hover:bg-blue-50/40 ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                                                            }`}
                                                    >
                                                        <td className="px-5 py-4 text-xs text-slate-300 font-mono text-center">{i + 1}</td>
                                                        {parsedData.columns.map((col) => (
                                                            <td
                                                                key={`${i}-${col}`}
                                                                className="px-5 py-4 whitespace-nowrap text-sm text-slate-700"
                                                            >
                                                                {row[col] || (
                                                                    <span className="text-slate-200 italic">—</span>
                                                                )}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="text-center py-16 border-2 border-dashed border-slate-100 rounded-xl">
                                        <FileText className="w-10 h-10 text-slate-200 mx-auto mb-3" />
                                        <p className="text-slate-400 font-medium">No rows found in this CSV file.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
        </div>
    );
}
