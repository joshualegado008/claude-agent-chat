/**
 * Agent Message Component - Displays a single agent message
 */

import { getAgentColor } from '@/lib/utils';
import { Bot, Brain } from 'lucide-react';

interface AgentMessageProps {
  agentName: string;
  content: string;
  thinking?: string | null;
  isStreaming?: boolean;
  showThinking?: boolean;
}

export function AgentMessage({
  agentName,
  content,
  thinking,
  isStreaming = false,
  showThinking = true,
}: AgentMessageProps) {
  const agentColor = getAgentColor(agentName);
  const colorClasses: Record<string, string> = {
    nova: 'bg-nova text-white border-nova',
    atlas: 'bg-atlas text-white border-atlas',
    gray: 'bg-gray-500 text-white border-gray-500',
  };

  return (
    <div className="fade-in space-y-3">
      {/* Agent Header */}
      <div className="flex items-center space-x-2">
        <div className={`p-2 rounded-full ${colorClasses[agentColor]}`}>
          <Bot className="w-5 h-5" />
        </div>
        <span className="font-bold text-lg">{agentName}</span>
        {isStreaming && (
          <span className="text-sm text-gray-500 animate-pulse">typing...</span>
        )}
      </div>

      {/* Thinking Content */}
      {showThinking && thinking && (
        <div className="ml-9 p-4 bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 rounded-r-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Brain className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
            <span className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
              Thinking...
            </span>
          </div>
          <p className="text-sm text-yellow-900 dark:text-yellow-100 whitespace-pre-wrap font-mono">
            {thinking}
          </p>
        </div>
      )}

      {/* Response Content */}
      <div className="ml-9">
        <div className={`p-4 rounded-lg border-2 ${
          agentColor === 'nova'
            ? 'bg-cyan-50 dark:bg-cyan-900/20 border-nova-light'
            : agentColor === 'atlas'
            ? 'bg-amber-50 dark:bg-amber-900/20 border-atlas-light'
            : 'bg-gray-50 dark:bg-gray-800 border-gray-300'
        }`}>
          <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed">
            {content}
          </p>
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1"></span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Typing Indicator - Shows animated dots when agent is preparing
 */
export function TypingIndicator({ agentName }: { agentName: string }) {
  const agentColor = getAgentColor(agentName);
  const colorClasses: Record<string, string> = {
    nova: 'bg-nova',
    atlas: 'bg-atlas',
    gray: 'bg-gray-500',
  };

  return (
    <div className="fade-in">
      <div className="flex items-center space-x-2">
        <div className={`p-2 rounded-full ${colorClasses[agentColor]} text-white`}>
          <Bot className="w-5 h-5" />
        </div>
        <span className="font-bold text-lg">{agentName}</span>
      </div>
      <div className="ml-9 mt-2 flex items-center space-x-2">
        <div className="flex space-x-1">
          <div className="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
          <div className="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
          <div className="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
        </div>
        <span className="text-sm text-gray-500">preparing response...</span>
      </div>
    </div>
  );
}
