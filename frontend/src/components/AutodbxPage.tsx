import React, { useState, useCallback, useEffect } from 'react';
import toast from 'react-hot-toast';
import { ArrowRight, Github, Play, CheckCircle2, CloudCog, Loader } from 'lucide-react';
import {
    databricksValidate,
    databricksDeploy,
    databricksRunConfigTable,
    databricksRunMigrationJob,
    fetchAutodbxFolders,
    uploadDatabricksConfigCsv // Import the new function
} from '../services/autodbxServices';

enum StepStatus {
    PENDING = 'pending',
    LOADING = 'loading',
    SUCCESS = 'success',
    FAILURE = 'failure',
}

interface Step {
    id: string;
    name: string;
    status: StepStatus;
    action: () => Promise<void>;
    canExecute: (currentSteps: Step[]) => boolean;
    buttonText: string;
    loadingText: string;
    icon: React.ElementType; // Type for Lucide React icons
    iconColorClass: (status: StepStatus) => string;
    message?: string;
}

const AutodbxPage: React.FC = () => {
    const [branchName, setBranchName] = useState<string>(''); // This can likely be removed now
    const [output, setOutput] = useState<string>('');
    const [globalLoading, setGlobalLoading] = useState<boolean>(false); // Used to disable all buttons during any operation
    const [runUrl, setRunUrl] = useState<string | null>(null);
    const [autodbxFolders, setAutodbxFolders] = useState<string[]>([]); // Moved up
    const [selectedFolder, setSelectedFolder] = useState<string>(''); // Moved up
    const [selectedCsvFile, setSelectedCsvFile] = useState<File | null>(null); // New state for selected CSV file

    const appendOutput = useCallback((chunk: string) => { // useCallback for appendOutput
        setOutput(prev => {
            const runUrlMatch = chunk.match(/Run URL: (https?:\/\/[^\s]+)/);
            if (runUrlMatch && runUrlMatch[1]) {
                setRunUrl(runUrlMatch[1]);
            }
            return prev + chunk;
        });
    }, []); // No dependencies, as setOutput from useState is stable

    const handleAction = useCallback(async (actionFn: () => Promise<void>, stepId: string) => { // useCallback for handleAction
        setGlobalLoading(true);
        setOutput(''); // Reset output console at the start of every action
        setOutput(prev => prev + `\n--- Starting ${stepId.replace(/([A-Z])/g, ' $1').trim()} ---\n`);
        setRunUrl(null); // Clear run URL for new actions

        const updateStep = (id: string, newStatus: StepStatus, message?: string) => {
            setSteps(prevSteps => prevSteps.map(step =>
                step.id === id ? { ...step, status: newStatus, message: message ?? step.message } : step
            ));
        };

        try {
            updateStep(stepId, StepStatus.LOADING);
            await actionFn();
            updateStep(stepId, StepStatus.SUCCESS);
            toast.success(`${stepId.replace(/([A-Z])/g, ' $1').trim()} completed!`);
        } catch (error: any) {
            const errorMessage = error?.message || 'An unknown error occurred.';
            let userFacingMessage = `${stepId.replace(/([A-Z])/g, ' $1').trim()} failed: ${errorMessage}`;
            let timelineStepMessage = `${stepId.replace(/([A-Z])/g, ' $1').trim()} failed.`; // Generic message for timeline

            // Specific handling for Terraform error
            if (errorMessage.includes("terraform") && errorMessage.includes("no such file or directory")) {
                userFacingMessage = `Validation failed: Terraform not found or executable. Please ensure Terraform is installed and in your system's PATH on the server where the backend runs.`;
                timelineStepMessage = `Validation failed (Terraform missing).`; // Specific, shorter timeline message
                toast.error(userFacingMessage, { duration: 8000 }); // Longer toast for actionable error
            } else {
                toast.error(userFacingMessage);
            }

            updateStep(stepId, StepStatus.FAILURE, timelineStepMessage); // Use generic or specific shorter message here
            appendOutput(`Error: ${errorMessage}\n`);
        } finally {
            setGlobalLoading(false);
            setOutput(prev => prev + `\n--- Finished ${stepId.replace(/([A-Z])/g, ' $1').trim()} ---\n`);
        }
    }, [appendOutput]); // Dependency on appendOutput

    const handleDatabricksValidate = useCallback(async () => { // useCallback for handleDatabricksValidate
        if (!selectedFolder) {
            toast.error('Please select an AutoDBx project folder.');
            return;
        }
        await handleAction(async () => {
            await databricksValidate(selectedFolder, appendOutput);
        }, 'validate');
    }, [selectedFolder, handleAction, appendOutput]); // Dependencies on handleAction, appendOutput

    const handleDatabricksDeploy = useCallback(async () => { // useCallback for handleDatabricksDeploy
        if (!selectedFolder) {
            toast.error('Please select an AutoDBx project folder.');
            return;
        }
        await handleAction(async () => {
            await databricksDeploy(selectedFolder, appendOutput);
        }, 'deploy');
    }, [selectedFolder, handleAction, appendOutput]); // Dependencies on handleAction, appendOutput

    const handleRunConfigTable = useCallback(async () => { // useCallback for handleRunConfigTable
        if (!selectedFolder) {
            toast.error('Please select an AutoDBx project folder.');
            return;
        }
        await handleAction(async () => {
            await databricksRunConfigTable(selectedFolder, appendOutput);
        }, 'runConfigTable');
    }, [selectedFolder, handleAction, appendOutput]); // Dependencies on handleAction, appendOutput

    const handleRunMigrationJob = useCallback(async () => { // useCallback for handleRunMigrationJob
        if (!selectedFolder) {
            toast.error('Please select an AutoDBx project folder.');
            return;
        }
        await handleAction(async () => {
            await databricksRunMigrationJob(selectedFolder, appendOutput);
        }, 'runMigrationJob');
    }, [selectedFolder, handleAction, appendOutput]); // Dependencies on handleAction, appendOutput

    const [steps, setSteps] = useState<Step[]>(() => []); // Initialize steps as empty, then use useEffect

    useEffect(() => { // Populate steps in useEffect to ensure latest handlers are used
        setSteps([
            {
                id: 'uploadConfig',
                name: 'Upload Databricks Config',
                status: StepStatus.PENDING,
                action: handleUploadCsv, // New action
                canExecute: () => !!selectedCsvFile, // Can execute if a file is selected
                buttonText: 'Upload Config',
                loadingText: 'Uploading...',
                icon: CloudCog, // Using CloudCog for config upload
                iconColorClass: (status) => {
                    switch (status) {
                        case StepStatus.SUCCESS: return 'text-green-500';
                        case StepStatus.FAILURE: return 'text-red-500';
                        case StepStatus.LOADING: return 'text-blue-500 animate-spin';
                        default: return 'text-gray-400';
                    }
                }
            },
            {
                id: 'validate',
                name: 'Validate Bundle',
                status: StepStatus.PENDING,
                action: handleDatabricksValidate,
                canExecute: (currentSteps) => currentSteps.find(s => s.id === 'uploadConfig')?.status === StepStatus.SUCCESS && !!selectedFolder, // Depends on upload and folder selection
                buttonText: 'Validate',
                loadingText: 'Validating...',
                icon: CheckCircle2,
                iconColorClass: (status) => {
                    switch (status) {
                        case StepStatus.SUCCESS: return 'text-green-500';
                        case StepStatus.FAILURE: return 'text-red-500';
                        case StepStatus.LOADING: return 'text-blue-500 animate-spin';
                        default: return 'text-gray-400';
                    }
                }
            },
            {
                id: 'deploy',
                name: 'Deploy Bundle',
                status: StepStatus.PENDING,
                action: handleDatabricksDeploy,
                canExecute: (currentSteps) => currentSteps.find(s => s.id === 'validate')?.status === StepStatus.SUCCESS,
                buttonText: 'Deploy',
                loadingText: 'Deploying...',
                icon: CloudCog,
                iconColorClass: (status) => {
                    switch (status) {
                        case StepStatus.SUCCESS: return 'text-green-500';
                        case StepStatus.FAILURE: return 'text-red-500';
                        case StepStatus.LOADING: return 'text-blue-500 animate-spin';
                        default: return 'text-gray-400';
                    }
                }
            },
            {
                id: 'runConfigTable',
                name: 'Run Config Table Job',
                status: StepStatus.PENDING,
                action: handleRunConfigTable,
                canExecute: (currentSteps) => currentSteps.find(s => s.id === 'deploy')?.status === StepStatus.SUCCESS,
                buttonText: 'Run Job',
                loadingText: 'Running...',
                icon: Play,
                iconColorClass: (status) => {
                    switch (status) {
                        case StepStatus.SUCCESS: return 'text-green-500';
                        case StepStatus.FAILURE: return 'text-red-500';
                        case StepStatus.LOADING: return 'text-blue-500 animate-spin';
                        default: return 'text-gray-400';
                    }
                }
            },
            {
                id: 'runMigrationJob',
                name: 'Run Migration Job',
                status: StepStatus.PENDING,
                action: handleRunMigrationJob,
                canExecute: (currentSteps) => currentSteps.find(s => s.id === 'runConfigTable')?.status === StepStatus.SUCCESS,
                buttonText: 'Run Job',
                loadingText: 'Running...',
                icon: Play,
                iconColorClass: (status) => {
                    switch (status) {
                        case StepStatus.SUCCESS: return 'text-green-500';
                        case StepStatus.FAILURE: return 'text-red-500';
                        case StepStatus.LOADING: return 'text-blue-500 animate-spin';
                        default: return 'text-gray-400';
                    }
                }
            }
        ]);
    }, [selectedFolder, handleDatabricksValidate, handleDatabricksDeploy, handleRunConfigTable, handleRunMigrationJob]); // Updated dependencies

    const openRunUrl = () => {
        if (runUrl) {
            window.open(runUrl, '_blank');
        }
    };

    // New useEffect to fetch folders
    useEffect(() => {
        const getFolders = async () => {
            const result = await fetchAutodbxFolders(); // Call the new service
            if (result.folders && result.folders.length > 0) {
                setAutodbxFolders(result.folders);
                setSelectedFolder(result.folders[0]); // Select the first folder by default
            } else if (result.error) {
                toast.error(`Failed to load AutoDBx folders: ${result.error}`);
            }
        };
        
        getFolders();
    }, []);

    const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files.length > 0) {
            setSelectedCsvFile(event.target.files[0]);
        } else {
            setSelectedCsvFile(null);
        }
    }, []);

    const handleUploadCsv = useCallback(async () => {
        if (!selectedCsvFile) {
            toast.error('Please select a CSV file to upload.');
            return;
        }
        await handleAction(async () => {
            const result = await uploadDatabricksConfigCsv(selectedCsvFile);
            if (result.returncode !== 0) {
                throw new Error(result.stderr || result.message || 'Failed to upload Databricks config CSV.');
            }
            // Optionally clear the file input after successful upload if needed
            // setSelectedCsvFile(null);
        }, 'uploadConfig');
    }, [selectedCsvFile, handleAction]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 py-12 transition-all duration-300 ease-in-out">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-300 ease-in-out">
                <div className="text-center mb-12 transition-all duration-300 ease-in-out">
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                        <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">AutoDBx</span> Operations
                    </h1>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                        Manage your Databricks bundles with a guided workflow.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Left Column: Output Console */}
                    <div className="bg-gray-900 text-white p-8 rounded-2xl shadow-lg border border-gray-700 h-full flex flex-col">
                        <div className="flex justify-between items-center mb-6"> {/* New flex container for header and button */}
                            <h2 className="text-2xl font-semibold text-gray-100">Output Console</h2>
                            {runUrl && (
                                <button
                                    onClick={openRunUrl}
                                    className="group inline-flex items-center justify-center px-4 py-2 text-base font-semibold text-white bg-blue-500 rounded-xl hover:bg-blue-600 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
                                >
                                    Open URL
                                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                                </button>
                            )}
                        </div>
                        <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-800 p-4 rounded-lg overflow-auto flex-grow border border-gray-700">
                            {output || 'No output yet. Start a workflow to see the results.'}
                        </pre>
                    </div>

                    {/* Right Column: Workflow Timeline */}
                    <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 shadow-lg h-full flex flex-col">
                        <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                            Workflow Steps
                        </h2>

                        {/* Databricks Config Upload Section */}
                        <div className="mb-8">
                            <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
                                <CloudCog className="inline-block mr-3 text-gray-500" size={20} />
                                Upload Databricks Configuration (CSV)
                            </h3>
                            <input
                                type="file"
                                accept=".csv"
                                onChange={handleFileChange}
                                className="w-full text-gray-700 bg-gray-50/70 p-2 border border-gray-300 rounded-md mb-4"
                                disabled={globalLoading}
                            />
                            <button
                                onClick={handleUploadCsv}
                                className={`group inline-flex items-center justify-center px-6 py-2 text-base font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md ${
                                    globalLoading || !selectedCsvFile
                                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                        : 'bg-blue-600 text-white hover:bg-blue-700 transform hover:scale-[1.02]'
                                }`}
                                disabled={globalLoading || !selectedCsvFile}
                            >
                                {globalLoading && steps.find(s => s.id === 'uploadConfig')?.status === StepStatus.LOADING ? (
                                    <Loader className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                    <CloudCog className="mr-2 h-4 w-4" />
                                )}
                                {globalLoading && steps.find(s => s.id === 'uploadConfig')?.status === StepStatus.LOADING ? 'Uploading...' : 'Upload Config'}
                            </button>
                        </div>

                        {/* Project Selection Section */}
                        <div className="mb-8">
                            <h3 className="text-xl font-semibold text-gray-700 mb-4 flex items-center">
                                <CloudCog className="inline-block mr-3 text-gray-500" size={20} />
                                Select AutoDBx Project
                            </h3>
                            <select
                                value={selectedFolder}
                                onChange={(e) => setSelectedFolder(e.target.value)}
                                className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-700 bg-gray-50/70"
                                disabled={globalLoading || autodbxFolders.length === 0}
                            >
                                {autodbxFolders.length === 0 && <option value="">Loading projects...</option>}
                                {autodbxFolders.map(folder => (
                                    <option key={folder} value={folder}>{folder}</option>
                                ))}
                            </select>
                        </div>

                        {/* Timeline for Databricks Bundle Actions */}
                        <div className="space-y-6 flex-grow">
                            {steps.map((step, index) => {
                                const IconComponent = step.icon;
                                const isCurrentStepLoading = step.status === StepStatus.LOADING;
                                const isDisabled = !step.canExecute(steps) || globalLoading;

                                return (
                                    <div key={step.id} className="flex items-start group">
                                        <div className="flex flex-col items-center mr-4">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                                                step.status === StepStatus.SUCCESS ? 'border-green-500 bg-green-100' :
                                                step.status === StepStatus.FAILURE ? 'border-red-500 bg-red-100' :
                                                step.status === StepStatus.LOADING ? 'border-blue-500 bg-blue-100' :
                                                'border-gray-300 bg-gray-100'
                                            } transition-all duration-300 ease-in-out`}>
                                                <IconComponent className={`h-4 w-4 ${step.iconColorClass(step.status)}`} />
                                            </div>
                                            {index < steps.length - 1 && (
                                                <div className={`h-10 w-0.5 ${
                                                    steps[index + 1].status !== StepStatus.PENDING ? 'bg-blue-300' : 'bg-gray-200'
                                                } transition-all duration-300 ease-in-out`} />
                                            )}
                                        </div>
                                        <div className="flex-grow">
                                            <div className={`text-lg font-medium ${
                                                step.status === StepStatus.SUCCESS ? 'text-gray-700' :
                                                step.status === StepStatus.FAILURE ? 'text-red-700' :
                                                step.status === StepStatus.LOADING ? 'text-blue-700' :
                                                'text-gray-500'
                                            } transition-all duration-300 ease-in-out`}>
                                                {step.name}
                                            </div>
                                            {step.message && (
                                                <p className="text-sm text-gray-600 mt-1">{step.message}</p>
                                            )}
                                            <button
                                                onClick={() => step.action()}
                                                className={`mt-2 group inline-flex items-center justify-center px-6 py-2 text-base font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md ${
                                                    isDisabled
                                                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                                        : 'bg-blue-600 text-white hover:bg-blue-700 transform hover:scale-[1.02]'
                                                }`}
                                                disabled={isDisabled}
                                            >
                                                {isCurrentStepLoading ? (
                                                    <Loader className="mr-2 h-4 w-4 animate-spin" />
                                                ) : (
                                                    <IconComponent className="mr-2 h-4 w-4" />
                                                )}
                                                {isCurrentStepLoading ? step.loadingText : step.buttonText}
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AutodbxPage;