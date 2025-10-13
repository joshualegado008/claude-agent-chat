/**
 * Conversation Controls - Pause, Resume, Stop buttons
 */

import { Pause, Play, Square, Info, MessageSquarePlus } from 'lucide-react';

interface ConversationControlsProps {
  isPaused: boolean;
  isComplete: boolean;
  isConnected: boolean;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onShowDashboard: () => void;
  onShowInject?: () => void;
}

export function ConversationControls({
  isPaused,
  isComplete,
  isConnected,
  onPause,
  onResume,
  onStop,
  onShowDashboard,
  onShowInject,
}: ConversationControlsProps) {
  if (isComplete) {
    return (
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 text-center">
        <p className="text-green-800 dark:text-green-200 font-medium">
          ✅ Conversation Complete
        </p>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 text-center">
        <p className="text-yellow-800 dark:text-yellow-200 font-medium">
          🔌 Connecting...
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {/* Pause/Resume Button */}
          {isPaused ? (
            <button
              onClick={onResume}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Resume</span>
            </button>
          ) : (
            <button
              onClick={onPause}
              className="flex items-center space-x-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors"
            >
              <Pause className="w-4 h-4" />
              <span>Pause</span>
            </button>
          )}

          {/* Stop Button */}
          <button
            onClick={onStop}
            className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
          >
            <Square className="w-4 h-4" />
            <span>Stop</span>
          </button>
        </div>

        <div className="flex items-center space-x-3">
          {/* Inject Content Button - Only show if paused or handler provided */}
          {onShowInject && isPaused && (
            <button
              onClick={onShowInject}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              <MessageSquarePlus className="w-4 h-4" />
              <span>Inject Content</span>
            </button>
          )}

          {/* Dashboard Button */}
          <button
            onClick={onShowDashboard}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Info className="w-4 h-4" />
            <span>View Insights</span>
          </button>
        </div>
      </div>

      {isPaused && (
        <div className="mt-3 text-center text-sm text-yellow-700 dark:text-yellow-300">
          ⏸️ Conversation paused. Click Resume to continue.
        </div>
      )}
    </div>
  );
}
