/**
 * Tool Use Message - Display when agent uses tools like fetch_url
 */

import { Globe, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface ToolUseMessageProps {
  message: string;
}

export function ToolUseMessage({ message }: ToolUseMessageProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Extract URL if present in message (format: "Fetching: https://...")
  const urlMatch = message.match(/https?:\/\/[^\s]+/);
  const url = urlMatch ? urlMatch[0] : null;
  const displayText = url ? `Fetching: ${url}` : message;

  return (
    <div className="my-4 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-900/20 rounded-r-lg overflow-hidden">
      <div
        className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
            <Globe className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
              🌐 Web Browsing
            </p>
            <p className="text-xs text-purple-700 dark:text-purple-300 font-mono">
              {displayText}
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        )}
      </div>

      {isExpanded && (
        <div className="px-4 py-3 border-t border-purple-200 dark:border-purple-800 bg-white dark:bg-gray-900">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 font-semibold">
            Tool Details:
          </p>
          <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono bg-gray-50 dark:bg-gray-800 p-3 rounded">
            {message}
          </pre>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 text-xs text-purple-600 dark:text-purple-400 hover:underline"
            >
              Open URL in new tab →
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolUseList({ toolUses }: { toolUses: string[] }) {
  if (toolUses.length === 0) return null;

  return (
    <div className="space-y-2 mb-4">
      {toolUses.map((toolUse, idx) => (
        <ToolUseMessage key={idx} message={toolUse} />
      ))}
    </div>
  );
}
