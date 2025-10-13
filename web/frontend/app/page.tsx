'use client';

import { useRouter } from 'next/navigation';
import { Plus, MessageSquare, Clock, TrendingUp } from 'lucide-react';
import { useConversations } from '@/hooks/useConversations';
import { Loading } from '@/components/Loading';
import { formatRelativeTime, formatNumber } from '@/lib/utils';

export default function DashboardPage() {
  const router = useRouter();
  const { data, isLoading, error } = useConversations(20);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                🤖 Claude Agent Chat
              </h1>
              <p className="text-slate-400 mt-1">
                Watch AI agents discuss topics in real-time
              </p>
            </div>

            <button
              onClick={() => router.push('/new')}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-cyan-600 to-purple-600 text-white rounded-lg font-medium hover:from-cyan-500 hover:to-purple-500 transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              <Plus className="w-5 h-5" />
              <span>New Conversation</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Conversations</p>
                <p className="text-3xl font-bold mt-1">{data?.count || 0}</p>
              </div>
              <MessageSquare className="w-12 h-12 text-cyan-400" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Turns</p>
                <p className="text-3xl font-bold mt-1">
                  {formatNumber(
                    data?.conversations.reduce((sum, conv) => sum + conv.total_turns, 0) || 0
                  )}
                </p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Tokens</p>
                <p className="text-3xl font-bold mt-1">
                  {formatNumber(
                    data?.conversations.reduce((sum, conv) => sum + conv.total_tokens, 0) || 0
                  )}
                </p>
              </div>
              <Clock className="w-12 h-12 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Conversations List */}
        <div className="bg-slate-800 rounded-xl shadow-lg overflow-hidden border border-slate-700">
          <div className="px-6 py-4 border-b border-slate-700">
            <h2 className="text-xl font-bold">Recent Conversations</h2>
          </div>

          {isLoading && (
            <div className="p-12">
              <Loading size="lg" />
            </div>
          )}

          {error && (
            <div className="p-12 text-center text-red-400">
              Failed to load conversations. Please try again.
            </div>
          )}

          {data && data.conversations.length === 0 && (
            <div className="p-12 text-center text-slate-400">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg mb-2">No conversations yet</p>
              <p className="text-sm">Start your first conversation to get started!</p>
            </div>
          )}

          {data && data.conversations.length > 0 && (
            <div className="divide-y divide-slate-700">
              {data.conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => router.push(`/conversation/${conv.id}`)}
                  className="w-full px-6 py-4 hover:bg-slate-700/50 transition-colors text-left"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-lg mb-1 truncate">
                        {conv.title}
                      </h3>
                      <p className="text-sm text-slate-400 mb-2">
                        {conv.agent_a_name} ↔ {conv.agent_b_name}
                      </p>

                      {/* Tags */}
                      {conv.tags && conv.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {conv.tags.slice(0, 3).map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-cyan-900/50 text-cyan-300 rounded text-xs border border-cyan-700"
                            >
                              {tag}
                            </span>
                          ))}
                          {conv.tags.length > 3 && (
                            <span className="px-2 py-1 bg-slate-700 text-slate-400 rounded text-xs">
                              +{conv.tags.length - 3} more
                            </span>
                          )}
                        </div>
                      )}

                      <div className="flex items-center space-x-4 text-sm text-slate-400">
                        <span>{conv.total_turns} turns</span>
                        <span>•</span>
                        <span>{formatNumber(conv.total_tokens)} tokens</span>
                        <span>•</span>
                        <span>{formatRelativeTime(conv.updated_at)}</span>
                      </div>
                    </div>

                    <div className="ml-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          conv.status === 'completed'
                            ? 'bg-green-900/50 text-green-300 border border-green-700'
                            : conv.status === 'paused'
                            ? 'bg-blue-900/50 text-blue-300 border border-blue-700'
                            : 'bg-yellow-900/50 text-yellow-300 border border-yellow-700'
                        }`}
                      >
                        {conv.status}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
