import {
    AlertCircle,
    ArrowRight,
    CheckCircle2,
    Download,
    FileSpreadsheet,
    Key,
    Upload,
} from 'lucide-react';
import { useRef, useState } from 'react';
import { ToastContainer, ToastMessage, createToastId } from '../components/Toast';
import { CsvData } from '../types';
import { generateSampleCredentialsCsv, generateSampleMigrationCsv, parseCsv } from '../utils/csvParser';

interface UploadPageProps {
    onProceed: (dataCsv: File, credentialsCsv: File, parsedData: CsvData) => void;
}

interface FileState {
    file: File | null;
    error: string | null;
}

export default function UploadPage({ onProceed }: UploadPageProps) {
    const [dataCsvState, setDataCsvState] = useState<FileState>({ file: null, error: null });
    const [credCsvState, setCredCsvState] = useState<FileState>({ file: null, error: null });
    const [toasts, setToasts] = useState<ToastMessage[]>([]);
    const [isDraggingData, setIsDraggingData] = useState(false);
    const [isDraggingCred, setIsDraggingCred] = useState(false);

    const dataInputRef = useRef<HTMLInputElement>(null);
    const credInputRef = useRef<HTMLInputElement>(null);

    const addToast = (type: 'success' | 'error', message: string) => {
        setToasts((prev) => [...prev, { id: createToastId(), type, message }]);
    };
    const dismissToast = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

    const validateCsvFile = (file: File): boolean => {
        if (!file.name.endsWith('.csv')) {
            return false;
        }
        if (file.size > 10 * 1024 * 1024) {
            return false;
        }
        return true;
    };

    const handleDataFile = (file: File) => {
        if (!validateCsvFile(file)) {
            setDataCsvState({ file: null, error: 'Please upload a valid .csv file under 10MB.' });
            addToast('error', 'Invalid migration file — must be a .csv under 10MB.');
            return;
        }
        setDataCsvState({ file, error: null });
        addToast('success', `Migration file "${file.name}" selected.`);
    };

    const handleCredFile = (file: File) => {
        if (!validateCsvFile(file)) {
            setCredCsvState({ file: null, error: 'Please upload a valid .csv file under 10MB.' });
            addToast('error', 'Invalid credentials file — must be a .csv under 10MB.');
            return;
        }
        setCredCsvState({ file, error: null });
        addToast('success', `Credentials file "${file.name}" selected.`);
    };

    const downloadSample = (type: 'migration' | 'credentials') => {
        const content =
            type === 'migration' ? generateSampleMigrationCsv() : generateSampleCredentialsCsv();
        const filename =
            type === 'migration' ? 'sample_migration.csv' : 'sample_credentials.csv';
        const blob = new Blob([content], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleProceed = async () => {
        if (!dataCsvState.file || !credCsvState.file) {
            addToast('error', 'Please upload both the migration CSV and credentials CSV.');
            return;
        }
        try {
            const text = await dataCsvState.file.text();
            const parsed = parseCsv(text);
            if (parsed.columns.length === 0) {
                addToast('error', 'Migration CSV appears to be empty or malformed.');
                return;
            }
            onProceed(dataCsvState.file, credCsvState.file, parsed);
        } catch {
            addToast('error', 'Failed to parse the migration CSV file.');
        }
    };

    const canProceed = !!dataCsvState.file && !!credCsvState.file;

    return (
        <div className="flex-1 bg-slate-50 py-12">
            <div className="w-full px-8 max-w-[1400px] mx-auto">
                <div className="text-center mb-10">
                    <h2 className="text-3xl font-bold text-slate-900 mb-2">Upload Your Files</h2>
                    <p className="text-slate-500 text-lg">
                        Provide your migration data and Databricks credentials to get started.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <UploadCard
                        title="Migration Data"
                        subtitle="Upload your .csv migration file"
                        icon={<FileSpreadsheet className="w-6 h-6 text-blue-600" />}
                        accentColor="blue"
                        file={dataCsvState.file}
                        error={dataCsvState.error}
                        isDragging={isDraggingData}
                        inputRef={dataInputRef}
                        sampleLabel="Download Sample Migration CSV"
                        onDownloadSample={() => downloadSample('migration')}
                        onFileSelect={handleDataFile}
                        onDragOver={(e) => { e.preventDefault(); setIsDraggingData(true); }}
                        onDragLeave={() => setIsDraggingData(false)}
                        onDrop={(e) => {
                            e.preventDefault();
                            setIsDraggingData(false);
                            const f = e.dataTransfer.files[0];
                            if (f) handleDataFile(f);
                        }}
                    />

                    <UploadCard
                        title="Databricks Credentials"
                        subtitle="Upload your credentials .csv file"
                        icon={<Key className="w-6 h-6 text-teal-600" />}
                        accentColor="teal"
                        file={credCsvState.file}
                        error={credCsvState.error}
                        isDragging={isDraggingCred}
                        inputRef={credInputRef}
                        sampleLabel="Download Sample Credentials CSV"
                        onDownloadSample={() => downloadSample('credentials')}
                        onFileSelect={handleCredFile}
                        onDragOver={(e) => { e.preventDefault(); setIsDraggingCred(true); }}
                        onDragLeave={() => setIsDraggingCred(false)}
                        onDrop={(e) => {
                            e.preventDefault();
                            setIsDraggingCred(false);
                            const f = e.dataTransfer.files[0];
                            if (f) handleCredFile(f);
                        }}
                    />
                </div>

                <div className="flex justify-center">
                    <button
                        onClick={handleProceed}
                        disabled={!canProceed}
                        className={`flex items-center gap-3 px-8 py-4 rounded-xl font-bold text-lg transition-all duration-200 shadow-md ${canProceed
                            ? 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg hover:-translate-y-0.5'
                            : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            }`}
                    >
                        Preview Data
                        <ArrowRight className="w-5 h-5" />
                    </button>
                </div>

                {!canProceed && (
                    <p className="text-center text-slate-400 text-sm mt-3">
                        Upload both files to continue
                    </p>
                )}
            </div>

            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
        </div>
    );
}

interface UploadCardProps {
    title: string;
    subtitle: string;
    icon: React.ReactNode;
    accentColor: 'blue' | 'teal';
    file: File | null;
    error: string | null;
    isDragging: boolean;
    inputRef: React.RefObject<HTMLInputElement>;
    sampleLabel: string;
    onDownloadSample: () => void;
    onFileSelect: (file: File) => void;
    onDragOver: (e: React.DragEvent) => void;
    onDragLeave: () => void;
    onDrop: (e: React.DragEvent) => void;
}

function UploadCard({
    title,
    subtitle,
    icon,
    accentColor,
    file,
    error,
    isDragging,
    inputRef,
    sampleLabel,
    onDownloadSample,
    onFileSelect,
    onDragOver,
    onDragLeave,
    onDrop,
}: UploadCardProps) {
    const colorMap = {
        blue: {
            border: isDragging ? 'border-blue-400 bg-blue-50' : file ? 'border-blue-300 bg-blue-50/50' : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/30',
            badge: 'bg-blue-100 text-blue-700',
            icon: 'text-blue-500',
            download: 'text-blue-600 hover:text-blue-800',
        },
        teal: {
            border: isDragging ? 'border-teal-400 bg-teal-50' : file ? 'border-teal-300 bg-teal-50/50' : 'border-slate-200 bg-white hover:border-teal-300 hover:bg-teal-50/30',
            badge: 'bg-teal-100 text-teal-700',
            icon: 'text-teal-500',
            download: 'text-teal-600 hover:text-teal-800',
        },
    };
    const c = colorMap[accentColor];

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-100">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${accentColor === 'blue' ? 'bg-blue-50' : 'bg-teal-50'}`}>
                        {icon}
                    </div>
                    <div>
                        <h3 className="font-semibold text-slate-800">{title}</h3>
                        <p className="text-sm text-slate-500">{subtitle}</p>
                    </div>
                </div>
            </div>

            <div className="p-5 space-y-4">
                <button
                    onClick={onDownloadSample}
                    className={`flex items-center gap-2 text-sm font-medium transition-colors ${c.download}`}
                >
                    <Download className="w-4 h-4" />
                    {sampleLabel}
                </button>

                <input
                    ref={inputRef}
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onFileSelect(f);
                    }}
                />

                <div
                    className={`relative border-2 border-dashed rounded-xl p-8 cursor-pointer transition-all duration-200 text-center ${c.border}`}
                    onClick={() => inputRef.current?.click()}
                    onDragOver={onDragOver}
                    onDragLeave={onDragLeave}
                    onDrop={onDrop}
                >
                    {file ? (
                        <div className="flex flex-col items-center gap-2">
                            <CheckCircle2 className={`w-10 h-10 ${c.icon}`} />
                            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${c.badge}`}>
                                {file.name}
                            </span>
                            <span className="text-xs text-slate-400">
                                {(file.size / 1024).toFixed(1)} KB &mdash; click to replace
                            </span>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center gap-2">
                            <Upload className={`w-10 h-10 ${c.icon} opacity-60`} />
                            <p className="text-slate-600 font-medium">
                                {isDragging ? 'Drop your file here' : 'Click to upload or drag & drop'}
                            </p>
                            <p className="text-xs text-slate-400">.csv files only, max 10MB</p>
                        </div>
                    )}
                </div>

                {error && (
                    <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}
