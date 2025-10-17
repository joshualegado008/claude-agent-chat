/**
 * Agent Message Component - Displays a single agent message
 */

import { getAgentColor } from '@/lib/utils';
import { Bot, Brain, ExternalLink } from 'lucide-react';
import { Source } from '@/types';

interface AgentMessageProps {
  agentName: string;
  content: string;
  thinking?: string | null;
  sources?: Source[];
  isStreaming?: boolean;
  showThinking?: boolean;
}

export function AgentMessage({
  agentName,
  content,
  thinking,
  sources,
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
            ? 'bg-chorus-secondary/30 dark:bg-chorus-secondary/30/20 border-nova-light'
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

          {/* Sources/Citations */}
          {sources && sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">
                Sources:
              </div>
              <div className="flex flex-wrap gap-2">
                {sources.map((source, idx) => (
                  <a
                    key={source.source_id || idx}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-200 shadow-sm hover:shadow"
                    title={source.excerpt || source.title}
                  >
                    <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-blue-500" />
                    <span className="text-gray-700 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 max-w-[200px] truncate">
                      {source.title}
                    </span>
                    {source.publisher && (
                      <span className="text-gray-400 dark:text-gray-500">
                        • {source.publisher}
                      </span>
                    )}
                  </a>
                ))}
              </div>
            </div>
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
