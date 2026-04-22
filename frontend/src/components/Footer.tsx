import { Database } from 'lucide-react';

export default function Footer() {
    return (
        <footer className="bg-slate-900 border-t border-slate-700 mt-auto">
            <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <Database className="w-4 h-4" />
                    <span>AutoDBx Migration Platform</span>
                </div>
                <span className="text-slate-500 text-sm">
                    &copy; {new Date().getFullYear()} AutoDBx. All rights reserved.
                </span>
            </div>
        </footer>
    );
}