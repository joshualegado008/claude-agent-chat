'use client';

import { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  conversationTitle: string;
  totalTurns: number;
  createdAt?: string;
  isDeleting?: boolean;
}

export function DeleteConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  conversationTitle,
  totalTurns,
  createdAt,
  isDeleting = false,
}: DeleteConfirmDialogProps) {
  const [confirmText, setConfirmText] = useState('');
  const isConfirmed = confirmText.toLowerCase() === 'yes';

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (isConfirmed) {
      onConfirm();
    }
  };

  const handleClose = () => {
    if (!isDeleting) {
      setConfirmText('');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Dialog */}
      <div className="relative bg-slate-800 rounded-xl shadow-2xl border-2 border-red-600 max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-6 h-6 text-red-500" />
            <h2 className="text-xl font-bold text-red-400">
              ⚠️  DELETE CONVERSATION?
            </h2>
          </div>
          {!isDeleting && (
            <button
              onClick={handleClose}
              className="p-1 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
            <p className="text-red-200 font-medium mb-3">
              You are about to PERMANENTLY DELETE:
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Title:</span>
                <span className="font-medium text-white max-w-xs truncate">
                  {conversationTitle}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Turns:</span>
                <span className="font-medium text-white">{totalTurns}</span>
              </div>
              {createdAt && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Created:</span>
                  <span className="font-medium text-white">
                    {new Date(createdAt).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-slate-300">
              This action <strong className="text-red-400">CANNOT</strong> be undone.
              All conversation data will be permanently removed from:
            </p>
            <ul className="text-sm text-slate-400 space-y-1 ml-4">
              <li>• PostgreSQL database (metadata & exchanges)</li>
              <li>• Qdrant vector database (semantic search index)</li>
              <li>• Context snapshots</li>
            </ul>
          </div>

          {/* Confirmation Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">
              Type <span className="text-red-400 font-bold">yes</span> to confirm deletion:
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="Type 'yes' here..."
              disabled={isDeleting}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              autoFocus
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-slate-700">
          <button
            onClick={handleClose}
            disabled={isDeleting}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!isConfirmed || isDeleting}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isDeleting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Deleting...</span>
              </>
            ) : (
              <span>Delete Permanently</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
