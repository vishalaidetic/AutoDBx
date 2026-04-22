import { Database, FileText, Loader2, Upload } from 'lucide-react';
import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { AWSDataResponse, fetchS3Data, uploadToS3 } from '../services/awsService';

export default function AWSDataViewer() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<AWSDataResponse | null>(null);
    const [s3Key, setS3Key] = useState<string>('');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            toast.error('Please select a file first');
            return;
        }

        setUploading(true);
        try {
            const { data: uploadData, error: uploadError } = await uploadToS3(file);
            if (uploadData) {
                setS3Key(uploadData.s3_key);
                toast.success('Uploaded successfully! Fetching data...');
                await handleFetchData(uploadData.s3_key);
            } else {
                toast.error(uploadError || 'Failed to upload to S3');
            }
        } catch (error: any) {
            toast.error(error.message);
        } finally {
            setUploading(false);
        }
    };

    const handleFetchData = async (key: string) => {
        setLoading(true);
        try {
            const { data: s3Data, error: s3Error } = await fetchS3Data(key);
            if (s3Data) {
                setData(s3Data);
            } else {
                toast.error(s3Error || 'Failed to fetch data from S3');
            }
        } catch (error: any) {
            toast.error(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-white">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
                            <Database className="w-8 h-8" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">AWS S3 Data Central</h1>
                            <p className="opacity-90">Upload, Process, and Visualize CSV/Excel datasets from S3</p>
                        </div>
                    </div>
                </div>

                <div className="p-8">
                    {/* Upload Section */}
                    <div className="mb-12">
                        <div className="max-w-2xl mx-auto space-y-4">
                            <label className="block text-sm font-semibold text-gray-700 uppercase tracking-wider text-center">
                                Upload and Process Dataset
                            </label>
                            <div className="relative group">
                                <input
                                    type="file"
                                    onChange={handleFileChange}
                                    className="hidden"
                                    id="s3-upload"
                                    accept=".csv,.xlsx,.xls"
                                />
                                <label
                                    htmlFor="s3-upload"
                                    className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-2xl cursor-pointer bg-gray-50 hover:bg-blue-50 hover:border-blue-300 transition-all group shadow-inner"
                                >
                                    <Upload className="w-12 h-12 text-gray-400 group-hover:text-blue-500 mb-2 transition-colors" />
                                    <span className="text-base font-medium text-gray-600">
                                        {file ? file.name : 'Click to select .csv or .xlsx dataset'}
                                    </span>
                                    <p className="text-xs text-gray-400 mt-2">Max file size: 10MB</p>
                                </label>
                            </div>
                            <button
                                onClick={handleUpload}
                                disabled={!file || uploading}
                                className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2 text-lg"
                            >
                                {uploading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Upload className="w-6 h-6" />}
                                {uploading ? 'Processing in S3...' : 'Upload & View Data'}
                            </button>
                        </div>
                    </div>

                    {/* Data Table */}
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-20 space-y-4">
                            <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
                            <p className="text-gray-500 font-medium">Downloading and parsing dataset from S3...</p>
                        </div>
                    ) : data ? (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="flex items-center justify-between">
                                <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                    <FileText className="w-6 h-6 text-blue-600" />
                                    Dataset Preview: {s3Key.split('/').pop()}
                                </h3>
                                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-bold">
                                    {data.data.length} Rows Loaded
                                </span>
                            </div>
                            <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm transition-all duration-300 ease-in-out">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            {data.columns.map((col) => (
                                                <th
                                                    key={col}
                                                    className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider"
                                                >
                                                    {col}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {data.data.map((row, i) => (
                                            <tr key={i} className="hover:bg-gray-50 transition-colors">
                                                {data.columns.map((col) => (
                                                    <td key={`${i}-${col}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                        {row[col]?.toString() || '—'}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-20 border-2 border-dashed border-gray-100 rounded-2xl">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <FileText className="w-8 h-8 text-gray-300" />
                            </div>
                            <p className="text-gray-400 font-medium">No dataset loaded. Upload a file above to begin.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
