'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, MessageSquare, Play } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useConversation } from '@/hooks/useConversations';
import { AgentMessage, TypingIndicator } from '@/components/AgentMessage';
import { ConversationControls } from '@/components/ConversationControls';
import { InterruptDashboard } from '@/components/InterruptDashboard';
import { InjectContentModal } from '@/components/InjectContentModal';
import { ToolUseList } from '@/components/ToolUseMessage';
import { LoadingScreen } from '@/components/Loading';
import { formatNumber, formatCost } from '@/lib/utils';
import { calculateHistoricalStats } from '@/lib/costCalculator';

export default function ConversationPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.id as string;

  // First, fetch conversation data via REST API
  const { data: conversationData, isLoading: isLoadingData } = useConversation(conversationId);

  // WebSocket for live streaming (only used when continuing)
  const {
    state,
    connect,
    pause,
    resume,
    stop,
    requestMetadata,
    inject,
  } = useWebSocket(conversationId);

  const [isLive, setIsLive] = useState(false); // Track if WebSocket is active
  const [showDashboard, setShowDashboard] = useState(false);
  const [showInjectModal, setShowInjectModal] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Calculate historical stats from exchanges (MUST be before early returns)
  const historicalStats = useMemo(() => {
    if (!conversationData || !conversationData.exchanges || conversationData.exchanges.length === 0) {
      return null;
    }

    return calculateHistoricalStats(
      conversationData.exchanges,
      conversationData.agent_a_name,
      conversationData.agent_a_model,
      conversationData.agent_b_name,
      conversationData.agent_b_model
    );
  }, [conversationData]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.exchanges.length, state.currentResponse]);

  // Auto-connect for brand new conversations (0 exchanges)
  useEffect(() => {
    if (conversationData && conversationData.exchanges.length === 0) {
      console.log('New conversation detected, auto-starting...');
      setIsLive(true);
      connect();
    }
  }, [conversationData, connect]);

  const handleContinue = () => {
    setIsLive(true);
    connect();
  };

  const handleInject = async (content: string) => {
    setIsInjecting(true);
    inject(content);
    // Close modal after a short delay to show feedback
    setTimeout(() => {
      setIsInjecting(false);
      setShowInjectModal(false);
    }, 500);
  };

  if (isLoadingData) {
    return <LoadingScreen message="Loading conversation..." />;
  }

  if (!conversationData) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-400 mb-2">Conversation Not Found</h2>
          <button
            onClick={() => router.push('/')}
            className="text-slate-400 hover:text-slate-200"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Use WebSocket data if live, otherwise use REST API data
  const exchanges = isLive ? state.exchanges : conversationData.exchanges;
  const title = isLive && state.title ? state.title : conversationData.title;
  const agentAName = isLive && state.agentAName ? state.agentAName : conversationData.agent_a_name;
  const agentBName = isLive && state.agentBName ? state.agentBName : conversationData.agent_b_name;
  const isComplete = isLive ? state.isComplete : conversationData.status === 'completed';
  const showContinueButton = !isLive && (conversationData.status === 'active' || conversationData.status === 'paused') && conversationData.total_turns < 20;
  const continueButtonText = conversationData.status === 'paused' ? 'Resume Conversation' : 'Continue Conversation';

  // Show stats if we have either live stats OR historical stats
  const showLiveStats = state.currentStats !== null;
  const showHistoricalStats = historicalStats !== null && !isLive;

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/')}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold">{title}</h1>
                <p className="text-sm text-slate-400">
                  {agentAName} ↔ {agentBName}
                </p>
              </div>
            </div>

            {/* Progress Stats */}
            {(showLiveStats || showHistoricalStats) && (
              <div className="flex items-center space-x-6 text-sm">
                <div className="text-center">
                  <div className="text-slate-400">Turns</div>
                  <div className="font-bold text-lg">
                    {showLiveStats
                      ? state.currentStats.session_stats?.current_turn || 0
                      : exchanges.length}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-slate-400">Tokens</div>
                  <div className="font-bold text-lg">
                    {showLiveStats
                      ? formatNumber(state.currentStats.session_stats?.projected_total_tokens || state.currentStats.total_tokens)
                      : formatNumber(historicalStats?.totalTokens || 0)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-slate-400">Cost</div>
                  <div className="font-bold text-lg">
                    {showLiveStats
                      ? formatCost(state.currentStats.total_cost)
                      : formatCost(historicalStats?.totalCost || 0)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="space-y-6">
          {/* Controls - Only show if live or complete */}
          {isLive && (
            <ConversationControls
              isPaused={state.isPaused}
              isComplete={isComplete}
              isConnected={state.isConnected}
              onPause={pause}
              onResume={resume}
              onStop={stop}
              onShowDashboard={() => {
                requestMetadata();
                setShowDashboard(true);
              }}
              onShowInject={() => setShowInjectModal(true)}
            />
          )}

          {/* Continue Button - Show for paused/stopped active conversations */}
          {showContinueButton && (
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    {conversationData.status === 'paused'
                      ? 'This conversation is paused'
                      : 'This conversation can be continued'}
                  </p>
                  <p className="text-sm text-slate-400">
                    {conversationData.total_turns} turns so far (max: 20)
                  </p>
                </div>
                <button
                  onClick={handleContinue}
                  className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-medium hover:from-green-700 hover:to-emerald-700 transition-all"
                >
                  <Play className="w-5 h-5" />
                  <span>{continueButtonText}</span>
                </button>
              </div>
            </div>
          )}

          {/* Messages Container */}
          <div className="bg-slate-800 rounded-xl shadow-lg p-6 min-h-[500px] max-h-[700px] overflow-y-auto border border-slate-700">
            {exchanges.length === 0 && !state.currentAgentName && (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <MessageSquare className="w-16 h-16 mb-4" />
                <p className="text-lg">Waiting for conversation to start...</p>
              </div>
            )}

            {/* Previous Exchanges */}
            {exchanges.map((exchange, idx) => (
              <div key={idx} className="mb-6">
                <AgentMessage
                  agentName={exchange.agent_name}
                  content={exchange.response_content}
                  thinking={exchange.thinking_content}
                  showThinking={true}
                />
              </div>
            ))}

            {/* Current Turn (Streaming) - Only when live */}
            {isLive && state.currentAgentName && (
              <div className="mb-6">
                {/* Tool Use Display */}
                {state.currentToolUses && state.currentToolUses.length > 0 && (
                  <ToolUseList toolUses={state.currentToolUses} />
                )}

                {state.currentThinking === '' && state.currentResponse === '' ? (
                  <TypingIndicator agentName={state.currentAgentName} />
                ) : (
                  <AgentMessage
                    agentName={state.currentAgentName}
                    content={state.currentResponse}
                    thinking={state.currentThinking}
                    isStreaming={true}
                    showThinking={true}
                  />
                )}
              </div>
            )}

            {/* Completed indicator */}
            {isComplete && !showContinueButton && (
              <div className="text-center py-4">
                <div className="inline-block px-6 py-3 bg-green-900/30 border border-green-700 rounded-lg">
                  <p className="text-green-300 font-medium">
                    ✅ Conversation Complete
                  </p>
                </div>
              </div>
            )}

            {/* Auto-scroll anchor */}
            <div ref={messagesEndRef} />
          </div>

          {/* Live Stats Panel (during streaming) */}
          {showLiveStats && state.currentStats && (
            <div className="bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-700">
              <h3 className="text-lg font-bold mb-4">📊 Turn Statistics</h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Token Breakdown */}
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-slate-400">
                    Tokens (This Turn)
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>Input:</span>
                      <span className="font-mono">{formatNumber(state.currentStats.input_tokens)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Output:</span>
                      <span className="font-mono">{formatNumber(state.currentStats.output_tokens)}</span>
                    </div>
                    {state.currentStats.thinking_tokens > 0 && (
                      <div className="flex justify-between">
                        <span>Thinking:</span>
                        <span className="font-mono">{formatNumber(state.currentStats.thinking_tokens)}</span>
                      </div>
                    )}
                    <div className="flex justify-between font-bold border-t pt-1">
                      <span>Total:</span>
                      <span className="font-mono">{formatNumber(state.currentStats.total_tokens)}</span>
                    </div>
                  </div>
                </div>

                {/* Context Window */}
                {state.currentStats.context_stats && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm text-slate-400">
                      Context Window
                    </h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Window Size:</span>
                        <span className="font-mono">{state.currentStats.context_stats.window_size} turns</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Exchanges:</span>
                        <span className="font-mono">{state.currentStats.context_stats.total_exchanges}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Context Tokens:</span>
                        <span className="font-mono">~{formatNumber(state.currentStats.context_stats.context_tokens_estimate)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Cost */}
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-slate-400">
                    Cost Analysis
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>This Turn:</span>
                      <span className="font-mono">{formatCost(state.currentStats.turn_cost)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Session:</span>
                      <span className="font-mono">{formatCost(state.currentStats.total_cost)}</span>
                    </div>
                    {state.currentStats.session_stats && (
                      <div className="flex justify-between text-slate-400">
                        <span>Projected:</span>
                        <span className="font-mono">{formatCost(state.currentStats.session_stats.projected_total_cost)}</span>
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Model: {state.currentStats.model_name}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Historical Stats Panel (for completed conversations) */}
          {showHistoricalStats && historicalStats && (
            <div className="bg-slate-800 rounded-xl shadow-lg p-6 border border-slate-700">
              <h3 className="text-lg font-bold mb-4">📊 Conversation Statistics</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Overall Stats */}
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-slate-400">
                    Overall Totals
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>Total Turns:</span>
                      <span className="font-mono font-bold">{exchanges.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Tokens:</span>
                      <span className="font-mono font-bold">{formatNumber(historicalStats.totalTokens)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Cost:</span>
                      <span className="font-mono font-bold text-green-400">{formatCost(historicalStats.totalCost)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400 text-xs mt-2">
                      <span>Avg per turn:</span>
                      <span className="font-mono">{formatNumber(Math.round(historicalStats.totalTokens / exchanges.length))} tokens</span>
                    </div>
                  </div>
                </div>

                {/* Per-Agent Breakdown */}
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-slate-400">
                    Per-Agent Breakdown
                  </h4>
                  <div className="space-y-3 text-sm">
                    {Object.entries(historicalStats.perAgentStats).map(([agentName, stats]) => (
                      <div key={agentName} className="border-l-2 border-cyan-500 pl-3">
                        <div className="font-medium text-cyan-400 mb-1">{agentName}</div>
                        <div className="flex justify-between text-xs">
                          <span>Tokens:</span>
                          <span className="font-mono">{formatNumber(stats.tokens)}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span>Cost:</span>
                          <span className="font-mono">{formatCost(stats.cost)}</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          Model: {stats.model?.includes('sonnet-4-5') ? 'Sonnet 4.5' : (stats.model || 'Unknown')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-700 text-xs text-slate-500">
                Note: Costs calculated using current model configuration. Historical exchanges may have used different models.
              </div>
            </div>
          )}

          {/* Error Display */}
          {state.error && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
              <p className="text-red-200 font-medium">
                ❌ Error: {state.error}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Interrupt Dashboard Modal */}
      {showDashboard && (
        <InterruptDashboard
          metadata={state.metadata}
          title={title}
          currentTurn={conversationData.total_turns}
          totalTokens={conversationData.total_tokens}
          totalCost={historicalStats?.totalCost || 0}
          onClose={() => setShowDashboard(false)}
          onResume={() => {
            setShowDashboard(false);
            if (isLive) resume();
          }}
          onStop={() => {
            setShowDashboard(false);
            if (isLive) stop();
          }}
        />
      )}

      {/* Inject Content Modal */}
      {showInjectModal && (
        <InjectContentModal
          onClose={() => setShowInjectModal(false)}
          onSubmit={handleInject}
          isSubmitting={isInjecting}
        />
      )}
    </div>
  );
}
