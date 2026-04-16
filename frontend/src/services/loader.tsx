// src/services/loader.tsx
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, ReactNode } from 'react';

type LoaderContextValue = {
  show: (message?: string) => void;
  hide: () => void;
};

const LoaderContext = createContext<LoaderContextValue | undefined>(undefined);

// Optional global singleton access (for non-React code)
let loaderSingleton: LoaderContextValue | null = null;
export const loader = {
  show: (msg?: string) => loaderSingleton?.show(msg),
  hide: () => loaderSingleton?.hide(),
};

export function LoaderProvider({ children }: { children: ReactNode }) {
  const [visible, setVisible] = useState(false);
  const [message, setMessage] = useState<string | undefined>(undefined);
  const timeoutRef = useRef<number | null>(null);

  const show = useCallback((msg?: string) => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setMessage(msg);
    setVisible(true);
  }, []);

  const hide = useCallback(() => {
    // small delay to avoid flicker
    timeoutRef.current = window.setTimeout(() => {
      setVisible(false);
      setMessage(undefined);
    }, 150);
  }, []);

  const value = useMemo(() => ({ show, hide }), [show, hide]);

  useEffect(() => {
    loaderSingleton = value;
    return () => {
      loaderSingleton = null;
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    };
  }, [value]);

  return (
    <LoaderContext.Provider value={value}>
      {children}
      {/* Removed the full-screen loading overlay */}
      {/*
      {visible && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="flex items-center gap-4 rounded-lg bg-white px-6 py-5 shadow-xl">
            <div className="h-6 w-6 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
            <div className="text-md font-semibold text-gray-800">{message || 'Loading...'}</div>
          </div>
        </div>
      )}
      */}
    </LoaderContext.Provider>
  );
}

export function useLoader() {
  const ctx = useContext(LoaderContext);
  if (!ctx) throw new Error('useLoader must be used within LoaderProvider');
  return ctx;
}