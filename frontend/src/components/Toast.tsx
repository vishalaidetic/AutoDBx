import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, X } from 'lucide-react';

export interface ToastMessage {
    id: string;
    type: 'success' | 'error';
    message: string;
}

interface ToastProps {
    toasts: ToastMessage[];
    onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastProps) {
    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
            {toasts.map((t) => (
                <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
            ))}
        </div>
    );
}

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: (id: string) => void }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        requestAnimationFrame(() => setVisible(true));
        const timer = setTimeout(() => {
            setVisible(false);
            setTimeout(() => onDismiss(toast.id), 300);
        }, 4000);
        return () => clearTimeout(timer);
    }, [toast.id, onDismiss]);

    return (
        <div
            className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border transition-all duration-300 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                } ${toast.type === 'success'
                    ? 'bg-white border-green-200 text-gray-800'
                    : 'bg-white border-red-200 text-gray-800'
                }`}
        >
            {toast.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
            ) : (
                <XCircle className="w-5 h-5 text-red-500 shrink-0" />
            )}
            <span className="text-sm font-medium max-w-xs">{toast.message}</span>
            <button
                onClick={() => onDismiss(toast.id)}
                className="ml-1 text-gray-400 hover:text-gray-600 transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

let toastCounter = 0;
export function createToastId() {
    return `toast-${++toastCounter}`;
}
