/**
 * Interrupt Dashboard - Beautiful metadata display when conversation is paused
 */

import { X, Heart, Brain, Users, TrendingUp, Sparkles, Tag } from 'lucide-react';
import type { ConversationMetadata } from '@/types';
import { getSentimentEmoji, getComplexityColor } from '@/lib/utils';

interface InterruptDashboardProps {
  metadata: ConversationMetadata | null;
  title: string;
  currentTurn: number;
  totalTokens: number;
  totalCost: number;
  onClose: () => void;
  onResume: () => void;
  onStop: () => void;
}

export function InterruptDashboard({
  metadata,
  title,
  currentTurn,
  totalTokens,
  totalCost,
  onClose,
  onResume,
  onStop,
}: InterruptDashboardProps) {
  if (!metadata) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">⏸️ Conversation Paused</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <p className="text-gray-600 dark:text-gray-400 mb-8">
            Metadata extraction not available. Configure OpenAI API key for rich insights.
          </p>

          <div className="flex space-x-3">
            <button
              onClick={onResume}
              className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
            >
              Resume
            </button>
            <button
              onClick={onStop}
              className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
            >
              Stop
            </button>
          </div>
        </div>
      </div>
    );
  }

  const sentiment = metadata.sentiment?.overall || 'Neutral';
  const sentimentScore = metadata.sentiment?.score || 0;
  const vibe = metadata.vibe || 'Analytical';
  const topics = metadata.topics || [];
  const entities = metadata.entities || [];
  const complexity = metadata.complexity?.level || 'Medium';
  const complexityScore = metadata.complexity?.score || 50;
  const keyPoints = metadata.key_points || [];
  const themes = metadata.themes || [];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-8 py-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-chorus-accent to-chorus-primary dark:from-gray-700 dark:to-gray-800">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-1">📊 Conversation Insights</h2>
              <p className="text-gray-600 dark:text-gray-400 text-sm">{title}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Quick Stats */}
          <div className="mt-4 flex items-center space-x-6 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Turn: </span>
              <span className="font-bold">{currentTurn}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Tokens: </span>
              <span className="font-bold">{totalTokens.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Cost: </span>
              <span className="font-bold">${totalCost.toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="space-y-6">
            {/* Vibe & Sentiment */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Current Vibe */}
              <div className="bg-gradient-to-br from-chorus-accent to-chorus-primary dark:from-chorus-secondary/20 dark:to-chorus-primary/20 rounded-xl p-6 border-2 border-chorus-secondary dark:border-chorus-secondary">
                <div className="flex items-center space-x-2 mb-3">
                  <Sparkles className="w-5 h-5 text-chorus-accent dark:text-chorus-accent" />
                  <h3 className="font-bold text-lg">Current Vibe</h3>
                </div>
                <div className="text-4xl mb-2">{getSentimentEmoji(vibe)}</div>
                <p className="text-2xl font-bold text-chorus-accent dark:text-chorus-accent">
                  {vibe}
                </p>
              </div>

              {/* Sentiment */}
              <div className="bg-gradient-to-br from-chorus-accent to-orange-100 dark:from-chorus-secondary/20 dark:to-orange-900/20 rounded-xl p-6 border-2 border-chorus-primary dark:border-chorus-secondary">
                <div className="flex items-center space-x-2 mb-3">
                  <Heart className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-bold text-lg">Sentiment</h3>
                </div>
                <p className="text-2xl font-bold mb-2 text-blue-900 dark:text-blue-100">
                  {sentiment}
                </p>

                {/* Sentiment Meter */}
                <div className="relative h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${sentimentScore}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Score: {sentimentScore}%
                </p>
              </div>
            </div>

            {/* Topics */}
            {topics.length > 0 && (
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-6 border-2 border-green-200 dark:border-green-700">
                <div className="flex items-center space-x-2 mb-4">
                  <Tag className="w-5 h-5 text-green-600 dark:text-green-400" />
                  <h3 className="font-bold text-lg">Topics Discussed</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-4 py-2 bg-green-600 text-white rounded-full font-medium shadow-sm hover:shadow-md transition-shadow"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Entities */}
            {entities.length > 0 && (
              <div className="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 rounded-xl p-6 border-2 border-orange-200 dark:border-orange-700">
                <div className="flex items-center space-x-2 mb-4">
                  <Users className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                  <h3 className="font-bold text-lg">Key Entities</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {entities.map((entity, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">
                          {entity.type === 'person' ? '👤' :
                           entity.type === 'organization' ? '🏢' :
                           entity.type === 'location' ? '📍' : '🏷️'}
                        </span>
                        <div>
                          <p className="font-medium">{entity.name}</p>
                          <p className="text-xs text-gray-500 capitalize">{entity.type}</p>
                        </div>
                      </div>
                      <span className="text-sm font-bold text-orange-600 dark:text-orange-400">
                        {entity.mentions}×
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Complexity */}
            <div className="bg-gradient-to-br from-indigo-50 to-violet-50 dark:from-indigo-900/20 dark:to-violet-900/20 rounded-xl p-6 border-2 border-indigo-200 dark:border-indigo-700">
              <div className="flex items-center space-x-2 mb-4">
                <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="font-bold text-lg">Complexity Level</h3>
              </div>
              <p className="text-xl font-bold mb-3 text-indigo-900 dark:text-indigo-100">
                {complexity}
              </p>

              {/* Complexity Bar */}
              <div className="relative h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ${
                    getComplexityColor(complexity) === 'green' ? 'bg-green-500' :
                    getComplexityColor(complexity) === 'yellow' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${complexityScore}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Score: {complexityScore}/100
              </p>
            </div>

            {/* Key Points */}
            {keyPoints.length > 0 && (
              <div className="bg-gradient-to-br from-chorus-accent to-orange-100 dark:from-chorus-secondary/20 dark:to-orange-900/20 rounded-xl p-6 border-2 border-chorus-primary dark:border-chorus-secondary">
                <div className="flex items-center space-x-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                  <h3 className="font-bold text-lg">Key Points</h3>
                </div>
                <ul className="space-y-2">
                  {keyPoints.map((point, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-teal-600 dark:text-teal-400 font-bold">•</span>
                      <span className="text-gray-700 dark:text-gray-300">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Themes */}
            {themes.length > 0 && (
              <div className="bg-gradient-to-br from-pink-50 to-rose-50 dark:from-pink-900/20 dark:to-rose-900/20 rounded-xl p-6 border-2 border-pink-200 dark:border-pink-700">
                <div className="flex items-center space-x-2 mb-4">
                  <Sparkles className="w-5 h-5 text-pink-600 dark:text-pink-400" />
                  <h3 className="font-bold text-lg">Emerging Themes</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {themes.map((theme, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-pink-600 text-white rounded-lg text-sm font-medium"
                    >
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-8 py-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <div className="flex space-x-3">
            <button
              onClick={onResume}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-medium transition-all transform hover:scale-[1.02] shadow-lg"
            >
              ▶️ Resume Conversation
            </button>
            <button
              onClick={onStop}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 text-white rounded-lg font-medium transition-all transform hover:scale-[1.02] shadow-lg"
            >
              ⏹️ Stop & Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
