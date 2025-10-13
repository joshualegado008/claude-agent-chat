/**
 * Inject Content Modal - Allow users to inject content mid-conversation
 */

import { useState } from 'react';
import { X, Send, Info } from 'lucide-react';

interface InjectContentModalProps {
  onClose: () => void;
  onSubmit: (content: string) => void;
  isSubmitting?: boolean;
}

export function InjectContentModal({
  onClose,
  onSubmit,
  isSubmitting = false,
}: InjectContentModalProps) {
  const [content, setContent] = useState('');

  const hasURL = /https?:\/\/[^\s]+/.test(content);

  const handleSubmit = () => {
    if (content.trim()) {
      onSubmit(content.trim());
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">💬 Inject Content into Conversation</h2>
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Inject new content, questions, or URLs into the ongoing conversation.
            Both agents will see this content and can incorporate it into their discussion.
          </p>

          {/* Textarea */}
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter your content here... You can include URLs, questions, or any information you want the agents to discuss."
            disabled={isSubmitting}
            className="w-full h-48 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 disabled:opacity-50"
            autoFocus
          />

          {/* URL Detection Hint */}
          {hasURL && (
            <div className="mt-3 flex items-start space-x-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <strong>URL Detected!</strong> The agents can use the <code className="px-1 py-0.5 bg-blue-100 dark:bg-blue-900 rounded">fetch_url</code> tool
                to automatically fetch and read content from any URLs you include.
              </div>
            </div>
          )}

          {/* Character Count */}
          <div className="mt-2 text-xs text-gray-500 text-right">
            {content.length} characters
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !content.trim()}
              className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Injecting...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Inject Content</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
