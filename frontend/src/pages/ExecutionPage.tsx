import {
    ArrowUpRight,
    CheckCircle2,
    ChevronRight,
    Clock,
    Info,
    Loader2,
    Play,
    Terminal,
    X,
    XCircle
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ToastContainer, ToastMessage, createToastId } from '../components/Toast';
import {
    createMigration,
    runMigrationStep
} from '../services/autodbxServices';
import { Stage, StageStatus } from '../types';

interface ExecutionPageProps {
    source: string;
    destination: string;
    dataCsvName: string;
    credCsvName: string;
    rowCount: number;
    selectedFolder: string;
}

const STAGE_DEFS: { id: string; name: string; shortName: string; description: string }[] = [
    {
        id: 'validate',
        name: 'Validate Bundle',
        shortName: 'Validate',
        description: 'Validates Databricks asset bundle configuration and Terraform state.',
    },
    {
        id: 'deploy',
        name: 'Deploy Bundle',
        shortName: 'Deploy',
        description: 'Deploys the Databricks asset bundle to the target workspace.',
    },
    {
        id: 'config_table',
        name: 'Config Table Job',
        shortName: 'Config Table',
        description: 'Runs the configuration table job to populate migration metadata.',
    },
    {
        id: 'migration_job',
        name: 'Migration Job',
        shortName: 'Migrate',
        description: 'Executes the full data migration job from source to destination.',
    },
];

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

export default function ExecutionPage({
    source,
    destination,
    dataCsvName,
    credCsvName,
    rowCount,
    selectedFolder,
}: ExecutionPageProps) {
    const [migrationId, setMigrationId] = useState<string | null>(null);
    const [stages, setStages] = useState<Stage[]>(() =>
        STAGE_DEFS.map((d) => ({
            id: d.id,
            name: d.name,
            status: 'pending',
            output: '',
            errorInfo: '',
        }))
    );
    const [runUrl, setRunUrl] = useState<string | null>(null);
    const [toasts, setToasts] = useState<ToastMessage[]>([]);
    const [activeStage, setActiveStage] = useState<string | null>(null);
    const outputRefs = useRef<Record<string, HTMLPreElement | null>>({});
    const modalOutputRef = useRef<HTMLPreElement | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [selectedStageId, setSelectedStageId] = useState<string | null>(null);

    const addToast = (type: 'success' | 'error', message: string) => {
        setToasts((prev) => [...prev, { id: createToastId(), type, message }]);
    };
    const dismissToast = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

    const appendToStage = useCallback((id: string, chunk: string) => {
        setStages((prev) =>
            prev.map((s) => {
                if (s.id !== id) return s;
                const urlMatch = chunk.match(/Run URL: (https?:\/\/[^\s]+)/);
                if (urlMatch) setRunUrl(urlMatch[1]);
                return { ...s, output: s.output + chunk + '\n' };
            })
        );
        setTimeout(() => {
            const el = outputRefs.current[id];
            if (el) el.scrollTop = el.scrollHeight;

            if (modalOutputRef.current && selectedStageId === id) {
                modalOutputRef.current.scrollTop = modalOutputRef.current.scrollHeight;
            }
        }, 50);
    }, [selectedStageId]);

    // 1. Initialize Migration
    useEffect(() => {
        async function init() {
            try {
                const { data, error } = await createMigration({
                    description: `Migration from ${source} to ${destination} using folder ${selectedFolder}`,
                });
                if (data) {
                    setMigrationId(data.id);
                } else {
                    addToast('error', error || 'Failed to initialize migration record.');
                }
            } catch (err) {
                addToast('error', 'Failed to initialize migration record.');
                console.error(err);
            }
        }
        if (!migrationId) init();
    }, [source, destination, selectedFolder, migrationId]);

    // 2. WebSocket Connection
    useEffect(() => {
        if (!migrationId) return;

        const ws = new WebSocket(`${WS_BASE_URL}/ws/migrations/${migrationId}`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            console.log('WS Message:', msg);

            switch (msg.type) {
                case 'init':
                    // Restore state if needed
                    break;
                case 'log':
                    appendToStage(msg.step, msg.log);
                    break;
                case 'step_status':
                    setStages((prev) =>
                        prev.map((s) => (s.id === msg.step ? { ...s, status: msg.status } : s))
                    );
                    if (msg.status === 'success') {
                        addToast('success', `${STAGE_DEFS.find((d) => d.id === msg.step)?.name} completed!`);
                    } else if (msg.status === 'failed') {
                        addToast('error', `${STAGE_DEFS.find((d) => d.id === msg.step)?.name} failed.`);
                    }
                    if (msg.status !== 'running') {
                        setActiveStage(null);
                    }
                    break;
                case 'error':
                    addToast('error', msg.error);
                    setActiveStage(null);
                    break;
            }
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
        };

        return () => ws.close();
    }, [migrationId, appendToStage]);

    const runStage = useCallback(
        async (stageId: string) => {
            if (!migrationId) return;

            setActiveStage(stageId);
            try {
                const { error } = await runMigrationStep(migrationId, stageId, selectedFolder);
                if (error) {
                    addToast('error', `Failed to trigger stage: ${error}`);
                    setActiveStage(null);
                }
            } catch (err: unknown) {
                const msg = err instanceof Error ? err.message : 'Unknown error';
                addToast('error', `Failed to trigger stage: ${msg}`);
                setActiveStage(null);
            }
        },
        [migrationId]
    );

    const getStageUnlocked = (stageId: string): boolean => {
        const idx = STAGE_DEFS.findIndex((d) => d.id === stageId);
        if (idx === 0) return true;
        return stages[idx - 1]?.status === 'success';
    };

    const overallStatus = (() => {
        if (stages.every((s) => s.status === 'success')) return 'complete';
        if (stages.some((s) => s.status === 'failed')) return 'failed';
        if (stages.some((s) => s.status === 'running' || s.status === 'loading')) return 'running';
        return 'idle';
    })();

    const completedCount = stages.filter((s) => s.status === 'success').length;

    return (
        <div className="flex-1 bg-slate-50 py-8">
            <div className="w-full px-6 space-y-6">
                <MetaDataBanner
                    source={source}
                    destination={destination}
                    dataCsvName={dataCsvName}
                    credCsvName={credCsvName}
                    rowCount={rowCount}
                    overallStatus={overallStatus}
                    completedCount={completedCount}
                    totalStages={STAGE_DEFS.length}
                    runUrl={runUrl}
                />

                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                        <h2 className="font-bold text-slate-800 flex items-center gap-2">
                            <Terminal className="w-5 h-5 text-blue-600" />
                            Execution Pipeline {migrationId && <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded text-slate-400 font-mono">ID: {migrationId}</span>}
                        </h2>
                        <div className="flex items-center gap-1.5 text-sm text-slate-500">
                            <span className="font-medium text-slate-700">{completedCount}</span>
                            <span>/</span>
                            <span>{STAGE_DEFS.length}</span>
                            <span>stages complete</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
                        {STAGE_DEFS.map((def, idx) => {
                            const stage = stages.find((s) => s.id === def.id)!;
                            const unlocked = getStageUnlocked(def.id);
                            const isActive = activeStage === def.id || stage.status === 'running' || stage.status === 'loading';
                            const globalLoading = activeStage !== null || stages.some(s => s.status === 'running' || s.status === 'loading');

                            return (
                                <StageColumn
                                    key={def.id}
                                    stageNum={idx + 1}
                                    def={def}
                                    stage={stage}
                                    unlocked={unlocked}
                                    isActive={isActive}
                                    globalLoading={globalLoading}
                                    outputRef={(el) => { outputRefs.current[def.id] = el; }}
                                    onRun={() => runStage(def.id)}
                                    onClick={() => setSelectedStageId(def.id)}
                                />
                            );
                        })}
                    </div>
                </div>
            </div>

            {selectedStageId && (
                <TerminalModal
                    def={STAGE_DEFS.find((d) => d.id === selectedStageId)!}
                    stage={stages.find((s) => s.id === selectedStageId)!}
                    onClose={() => setSelectedStageId(null)}
                    outputRef={modalOutputRef}
                />
            )}

            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
        </div>
    );
}

interface MetaDataBannerProps {
    source: string;
    destination: string;
    dataCsvName: string;
    credCsvName: string;
    rowCount: number;
    overallStatus: string;
    completedCount: number;
    totalStages: number;
    runUrl: string | null;
}

function MetaDataBanner({
    source,
    destination,
    dataCsvName,
    credCsvName,
    rowCount,
    overallStatus,
    completedCount,
    totalStages,
    runUrl,
}: MetaDataBannerProps) {
    const statusConfig = {
        idle: { label: 'Ready to Run', color: 'bg-slate-100 text-slate-600' },
        running: { label: 'Running...', color: 'bg-blue-100 text-blue-700' },
        complete: { label: 'All Stages Complete', color: 'bg-green-100 text-green-700' },
        failed: { label: 'Stage Failed', color: 'bg-red-100 text-red-700' },
    };
    const sc = statusConfig[overallStatus as keyof typeof statusConfig] ?? statusConfig.idle;

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-start justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 rounded-lg">
                        <Info className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                        <h2 className="font-bold text-slate-800">Migration Metadata</h2>
                        <p className="text-sm text-slate-500">Session overview and current status</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {runUrl && (
                        <a
                            href={runUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                        >
                            Open Run URL
                            <ArrowUpRight className="w-4 h-4" />
                        </a>
                    )}
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${sc.color}`}>
                        {sc.label}
                    </span>
                </div>
            </div>

            <div className="mt-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                <MetaItem label="Source" value={source} />
                <MetaItem label="Destination" value={destination} />
                <MetaItem label="Migration File" value={dataCsvName} />
                <MetaItem label="Credentials File" value={credCsvName} />
                <MetaItem label="Records" value={`${rowCount} rows`} />
            </div>

            <div className="mt-5">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                    <span>Pipeline Progress</span>
                    <span>{Math.round((completedCount / totalStages) * 100)}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                    <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${(completedCount / totalStages) * 100}%` }}
                    />
                </div>
            </div>
        </div>
    );
}

function MetaItem({ label, value }: { label: string; value: string }) {
    return (
        <div className="bg-slate-50 rounded-xl px-4 py-3 min-w-0">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-0.5">{label}</p>
            <p className="text-sm font-semibold text-slate-700 truncate" title={value}>{value}</p>
        </div>
    );
}

interface StageColumnProps {
    stageNum: number;
    def: (typeof STAGE_DEFS)[number];
    stage: Stage;
    unlocked: boolean;
    isActive: boolean;
    globalLoading: boolean;
    outputRef: (el: HTMLPreElement | null) => void;
    onRun: () => void;
    onClick: () => void;
}

function StageColumn({
    stageNum,
    def,
    stage,
    unlocked,
    isActive,
    globalLoading,
    outputRef,
    onRun,
    onClick,
}: StageColumnProps) {
    const statusMap: Record<StageStatus, { icon: React.ReactNode; label: string; labelColor: string; bg: string }> = {
        pending: {
            icon: <Clock className="w-4 h-4 text-slate-400" />,
            label: 'Pending',
            labelColor: 'text-slate-400',
            bg: 'bg-slate-100',
        },
        loading: {
            icon: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
            label: 'Running',
            labelColor: 'text-blue-600',
            bg: 'bg-blue-50',
        },
        running: {
            icon: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
            label: 'Running',
            labelColor: 'text-blue-600',
            bg: 'bg-blue-50',
        },
        success: {
            icon: <CheckCircle2 className="w-4 h-4 text-green-500" />,
            label: 'Success',
            labelColor: 'text-green-600',
            bg: 'bg-green-50',
        },
        failure: {
            icon: <XCircle className="w-4 h-4 text-red-500" />,
            label: 'Failed',
            labelColor: 'text-red-600',
            bg: 'bg-red-50',
        },
        failed: {
            icon: <XCircle className="w-4 h-4 text-red-500" />,
            label: 'Failed',
            labelColor: 'text-red-600',
            bg: 'bg-red-50',
        },
    };

    const sm = statusMap[stage.status as StageStatus] || statusMap.pending;
    const canRun = unlocked && !globalLoading && stage.status !== 'running' && stage.status !== 'loading';
    const isCompleted = stage.status === 'success';

    return (
        <div
            onClick={onClick}
            className={`flex flex-col p-5 gap-4 transition-all cursor-pointer hover:shadow-inner border-r border-transparent hover:border-slate-200 ${isActive ? 'bg-blue-50/50' : isCompleted ? 'bg-green-50/20' : 'hover:bg-slate-100/50'
                }`}
        >
            <div className="flex items-start justify-between gap-2">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            Stage {stageNum}
                        </span>
                        {!unlocked && (
                            <span className="text-xs text-slate-300">&mdash; locked</span>
                        )}
                    </div>
                    <h3 className="font-bold text-slate-800 text-sm leading-tight">{def.name}</h3>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{def.description}</p>
                </div>
                <div className={`shrink-0 p-1.5 rounded-lg ${sm.bg}`}>{sm.icon}</div>
            </div>

            <div
                className={`rounded-lg px-3 py-2 flex items-center gap-2 border ${stage.status === 'success'
                    ? 'bg-green-50 border-green-200'
                    : (stage.status === 'failure' || stage.status === 'failed')
                        ? 'bg-red-50 border-red-200'
                        : (stage.status === 'loading' || stage.status === 'running')
                            ? 'bg-blue-50 border-blue-200'
                            : 'bg-slate-50 border-slate-200'
                    }`}
            >
                {sm.icon}
                <span className={`text-xs font-semibold ${sm.labelColor}`}>{sm.label}</span>
                {(stage.status === 'failure' || stage.status === 'failed') && stage.errorInfo && (
                    <span className="text-xs text-red-500 ml-1 truncate" title={stage.errorInfo}>
                        — {stage.errorInfo.length > 30 ? stage.errorInfo.slice(0, 30) + '…' : stage.errorInfo}
                    </span>
                )}
            </div>

            <div>
                <div className="flex items-center gap-1.5 mb-1.5">
                    <Terminal className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Stream Output
                    </span>
                </div>
                <pre
                    ref={outputRef}
                    className="bg-slate-900 text-slate-100 text-xs font-mono rounded-xl p-3 h-44 overflow-auto whitespace-pre-wrap leading-relaxed border border-slate-700"
                >
                    {stage.output || (
                        <span className="text-slate-500">
                            {unlocked ? 'Ready. Click Run to start.' : 'Waiting for previous stage…'}
                        </span>
                    )}
                </pre>
            </div>

            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onRun();
                }}
                disabled={!canRun}
                className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-bold text-sm transition-all ${!canRun
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    : isCompleted
                        ? 'bg-green-600 text-white hover:bg-green-700 shadow-sm hover:shadow-md'
                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md'
                    }`}
            >
                {(stage.status === 'loading' || stage.status === 'running') ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Running…
                    </>
                ) : isCompleted ? (
                    <>
                        <CheckCircle2 className="w-4 h-4" />
                        Re-run
                    </>
                ) : (
                    <>
                        <Play className="w-4 h-4" />
                        Run
                        <ChevronRight className="w-3.5 h-3.5" />
                    </>
                )}
            </button>
        </div>
    );
}

interface TerminalModalProps {
    def: (typeof STAGE_DEFS)[number];
    stage: Stage;
    onClose: () => void;
    outputRef: React.RefObject<HTMLPreElement>;
}

function TerminalModal({ def, stage, onClose, outputRef }: TerminalModalProps) {
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    // Scroll to bottom on open
    useEffect(() => {
        if (outputRef.current) {
            outputRef.current.scrollTop = outputRef.current.scrollHeight;
        }
    }, [outputRef]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10">
            <div
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
                onClick={onClose}
            />
            <div className="relative w-full max-w-5xl h-full max-h-[80vh] bg-slate-950 rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-800 animate-in fade-in zoom-in duration-200">
                {/* Modal Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Terminal className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-100 flex items-center gap-2">
                                {def.name}
                                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">Terminal Output</span>
                            </h3>
                            <p className="text-xs text-slate-500">{def.description}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-100 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Modal Body / Terminal */}
                <div className="flex-1 overflow-hidden p-6 relative">
                    <div className="absolute top-0 left-0 w-full h-10 bg-gradient-to-b from-slate-950 to-transparent pointer-events-none z-10" />
                    <pre
                        ref={outputRef}
                        className="h-full overflow-auto text-sm font-mono text-slate-300 whitespace-pre-wrap leading-relaxed scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent pr-4 pt-4"
                    >
                        <div className="flex items-center gap-2 text-blue-400 mb-4 font-bold border-b border-blue-400/20 pb-2">
                            <ChevronRight className="w-4 h-4" />
                            Initializing {def.shortName} stream...
                        </div>
                        {stage.output || (
                            <span className="text-slate-600 block italic">
                                [System] No output generated yet for this stage.
                                Waiting for execution to begin...
                            </span>
                        )}
                    </pre>
                    <div className="absolute bottom-0 left-0 w-full h-10 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none z-10" />
                </div>

                {/* Modal Footer */}
                <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/30 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                            <div className={`w-2 h-2 rounded-full ${stage.status === 'running' ? 'bg-blue-500 animate-pulse' : stage.status === 'success' ? 'bg-green-500' : 'bg-slate-600'}`} />
                            Status: <span className="capitalize">{stage.status}</span>
                        </div>
                    </div>
                    <p className="text-[10px] text-slate-600 font-mono">
                        Press ESC to close
                    </p>
                </div>
            </div>
        </div>
    );
}
