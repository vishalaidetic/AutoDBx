import React, { useState, useEffect } from 'react';
import { X, Save, GitBranch, FolderOpen, Link2 } from 'lucide-react';

interface CloneConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (repoUrl: string, baseDir: string, branchName: string) => void;
    initialRepoUrl: string;
    initialBaseDir: string;
    initialBranchName: string;
}

const CloneConfigModal: React.FC<CloneConfigModalProps> = ({
    isOpen,
    onClose,
    onSave,
    initialRepoUrl,
    initialBaseDir,
    initialBranchName,
}) => {
    const [repoUrl, setRepoUrl] = useState(initialRepoUrl);
    const [baseDir, setBaseDir] = useState(initialBaseDir);
    const [branchName, setBranchName] = useState(initialBranchName);

    // Update internal state when initial values change (e.g., when modal is opened with new initial values)
    useEffect(() => {
        setRepoUrl(initialRepoUrl);
        setBaseDir(initialBaseDir);
        setBranchName(initialBranchName);
    }, [initialRepoUrl, initialBaseDir, initialBranchName]);

    if (!isOpen) return null;

    const handleSave = () => {
        onSave(repoUrl.trim(), baseDir.trim(), branchName.trim());
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm transition-opacity duration-300 ease-in-out">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-gray-200/50 w-full max-w-md mx-auto transform scale-95 opacity-0 animate-fade-in-up">
                <div className="flex justify-between items-center mb-6 border-b border-gray-200 pb-4">
                    <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                        <GitBranch className="h-6 w-6 mr-3 text-blue-600" />
                        Configure Repository Clone
                    </h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700 transition-colors duration-200">
                        <X size={24} />
                    </button>
                </div>

                <div className="space-y-4 mb-8">
                    <div>
                        <label htmlFor="repoUrl" className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <Link2 className="h-4 w-4 mr-2 text-gray-500" />
                            Repository URL
                        </label>
                        <input
                            id="repoUrl"
                            type="text"
                            value={repoUrl}
                            onChange={(e) => setRepoUrl(e.target.value)}
                            placeholder="e.g., https://github.com/user/repo.git"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-gray-700 bg-gray-50/70"
                        />
                    </div>
                    <div>
                        <label htmlFor="baseDir" className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <FolderOpen className="h-4 w-4 mr-2 text-gray-500" />
                            Base Directory
                        </label>
                        <input
                            id="baseDir"
                            type="text"
                            value={baseDir}
                            onChange={(e) => setBaseDir(e.target.value)}
                            placeholder="e.g., /home/user/projects"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-gray-700 bg-gray-50/70"
                        />
                    </div>
                    <div>
                        <label htmlFor="branchName" className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <GitBranch className="h-4 w-4 mr-2 text-gray-500" />
                            Branch Name (Optional)
                        </label>
                        <input
                            id="branchName"
                            type="text"
                            value={branchName}
                            onChange={(e) => setBranchName(e.target.value)}
                            placeholder="e.g., main or my-feature-branch"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-gray-700 bg-gray-50/70"
                        />
                    </div>
                </div>

                <div className="flex justify-end space-x-3">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors duration-200"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="group inline-flex items-center justify-center px-6 py-2 text-base font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-md"
                    >
                        <Save className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                        Save Configuration
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CloneConfigModal;
