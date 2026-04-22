import React, { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import ExecutionPage from '../pages/ExecutionPage';
import PreviewPage from '../pages/PreviewPage';
import UploadPage from '../pages/UploadPage';
import { fetchAutodbxFolders, uploadDatabricksConfigCsv } from '../services/autodbxServices';
import { AppState, CsvData } from '../types';
import Footer from './Footer';

const AutodbxPage: React.FC = () => {
    const [state, setState] = useState<AppState>({
        currentPage: 'upload',
        dataCsv: null,
        credentialsCsv: null,
        parsedData: null,
        parsedCredentials: null,
        source: '',
        destination: '',
        selectedFolder: '',
    });

    const handleUploadComplete = async (dataCsv: File, credentialsCsv: File, parsedData: CsvData) => {
        const credText = await credentialsCsv.text();
        const { parseCsv } = await import('../utils/csvParser');
        const parsedCredentials = parseCsv(credText);

        setState(prev => ({
            ...prev,
            dataCsv,
            credentialsCsv,
            parsedData,
            parsedCredentials,
            currentPage: 'preview'
        }));
    };

    const handlePreviewProceed = async (source: string, destination: string) => {
        if (!state.credentialsCsv) return;

        try {
            // Upload credentials to session before moving to execution
            const { data, error } = await uploadDatabricksConfigCsv(state.credentialsCsv);
            if (data) {
                setState(prev => ({
                    ...prev,
                    source,
                    destination,
                    currentPage: 'execution'
                }));
            } else {
                toast.error(error || 'Failed to apply credentials');
            }
        } catch (err: any) {
            toast.error(err.message || 'Error uploading credentials');
        }
    };

    const handleBackToUpload = () => {
        setState(prev => ({ ...prev, currentPage: 'upload' }));
    };

    const renderPage = () => {
        switch (state.currentPage) {
            case 'upload':
                return <UploadPage onProceed={handleUploadComplete} />;
            case 'preview':
                return (
                    <PreviewPage
                        parsedData={state.parsedData!}
                        parsedCredentials={state.parsedCredentials!}
                        dataCsvName={state.dataCsv!.name}
                        onProceed={handlePreviewProceed}
                        onCancel={handleBackToUpload}
                    />
                );
            case 'execution':
                return (
                    <ExecutionPage
                        source={state.source}
                        destination={state.destination}
                        dataCsvName={state.dataCsv!.name}
                        credCsvName={state.credentialsCsv!.name}
                        rowCount={state.parsedData!.rows.length}
                        selectedFolder={state.selectedFolder}
                    />
                );
            default:
                return <UploadPage onProceed={handleUploadComplete} />;
        }
    };

    return (
        <div className="min-h-screen flex flex-col bg-slate-50">
            {/* Stepper Indicator */}
            <div className="bg-white border-b border-slate-200">
                <div className="w-full px-6 py-4">
                    <div className="flex items-center justify-center gap-4 text-sm font-bold">
                        <StepItem
                            num={1}
                            label="Upload"
                            active={state.currentPage === 'upload'}
                            complete={state.currentPage !== 'upload'}
                        />
                        <div className="h-0.5 w-12 bg-slate-100" />
                        <StepItem
                            num={2}
                            label="Preview"
                            active={state.currentPage === 'preview'}
                            complete={state.currentPage === 'execution'}
                        />
                        <div className="h-0.5 w-12 bg-slate-100" />
                        <StepItem
                            num={3}
                            label="Execution"
                            active={state.currentPage === 'execution'}
                            complete={false}
                        />
                    </div>
                </div>
            </div>

            <main className="flex-grow flex flex-col">
                {renderPage()}
            </main>

            <Footer />
        </div>
    );
};

function StepItem({ num, label, active, complete }: { num: number; label: string; active: boolean; complete: boolean }) {
    return (
        <div className={`flex items-center gap-2 ${active ? 'text-blue-600' : complete ? 'text-green-600' : 'text-slate-400'}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border-2 ${active ? 'border-blue-600 bg-blue-50' :
                complete ? 'border-green-600 bg-green-50' :
                    'border-slate-200 bg-slate-50'
                }`}>
                {num}
            </div>
            <span>{label}</span>
        </div>
    );
}

export default AutodbxPage;