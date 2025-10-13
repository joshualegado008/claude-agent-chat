/**
 * WebSocket Hook - Real-time conversation streaming
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  WebSocketMessage,
  WebSocketCommand,
  Exchange,
  TokenStats,
  ConversationMetadata,
} from '@/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || process.env.WS_URL || 'ws://localhost:8000';

export interface ConversationState {
  conversationId: string;
  title: string;
  agentAName: string;
  agentBName: string;
  currentTurn: number;
  exchanges: Exchange[];
  isConnected: boolean;
  isReady: boolean;
  isPaused: boolean;
  isComplete: boolean;
  error: string | null;

  // Current turn state
  currentAgentName: string | null;
  currentThinking: string;
  currentResponse: string;
  currentStats: TokenStats | null;
  currentToolUses: string[]; // Tool uses for current turn

  // Metadata
  metadata: ConversationMetadata | null;
}

export interface UseWebSocketResult {
  state: ConversationState;
  connect: () => void;
  disconnect: () => void;
  sendCommand: (command: WebSocketCommand) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  requestMetadata: () => void;
  inject: (content: string) => void;
}

export function useWebSocket(conversationId: string): UseWebSocketResult {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const shouldReconnectRef = useRef<boolean>(true); // Track if we should auto-reconnect

  const [state, setState] = useState<ConversationState>({
    conversationId,
    title: '',
    agentAName: '',
    agentBName: '',
    currentTurn: 0,
    exchanges: [],
    isConnected: false,
    isReady: false,
    isPaused: false,
    isComplete: false,
    error: null,
    currentAgentName: null,
    currentThinking: '',
    currentResponse: '',
    currentStats: null,
    currentToolUses: [],
    metadata: null,
  });

  const sendCommand = useCallback((command: WebSocketCommand) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command }));
    }
  }, []);

  const pause = useCallback(() => {
    sendCommand('pause');
    setState(prev => ({ ...prev, isPaused: true }));
  }, [sendCommand]);

  const resume = useCallback(() => {
    sendCommand('resume');
    setState(prev => ({ ...prev, isPaused: false }));
  }, [sendCommand]);

  const stop = useCallback(() => {
    sendCommand('stop');
  }, [sendCommand]);

  const requestMetadata = useCallback(() => {
    sendCommand('get_metadata');
  }, [sendCommand]);

  const inject = useCallback((content: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'inject', content }));
    }
  }, []);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'conversation_loaded':
          setState(prev => ({
            ...prev,
            title: message.data.title,
            agentAName: message.data.agent_a_name,
            agentBName: message.data.agent_b_name,
            currentTurn: message.data.current_turn,
            exchanges: message.data.exchanges || [],
          }));
          break;

        case 'ready':
          setState(prev => ({ ...prev, isReady: true }));
          break;

        case 'turn_start':
          setState(prev => ({
            ...prev,
            currentAgentName: message.agent_name || null,
            currentThinking: '',
            currentResponse: '',
            currentStats: null,
            currentToolUses: [],
          }));
          break;

        case 'thinking_start':
          // Thinking started - no action needed, just wait for chunks
          break;

        case 'thinking_chunk':
          setState(prev => ({
            ...prev,
            currentThinking: prev.currentThinking + (message.chunk || ''),
          }));
          break;

        case 'response_chunk':
          setState(prev => ({
            ...prev,
            currentResponse: prev.currentResponse + (message.chunk || ''),
          }));
          break;

        case 'turn_complete':
          if (message.stats) {
            setState(prev => ({
              ...prev,
              currentStats: message.stats || null,
              currentAgentName: null,        // Clear current agent after completion
              currentThinking: '',            // Clear thinking content
              currentResponse: '',            // Clear response content
              exchanges: [
                ...prev.exchanges,
                {
                  turn_number: message.turn || 0,
                  agent_name: message.agent_name || '',
                  thinking_content: message.thinking || null,
                  response_content: message.response || '',
                  tokens_used: message.stats?.total_tokens || 0,
                  created_at: new Date().toISOString(),
                },
              ],
            }));
          }
          break;

        case 'conversation_complete':
          shouldReconnectRef.current = false; // Don't reconnect when complete
          setState(prev => ({
            ...prev,
            isComplete: true,
            currentAgentName: null,
          }));
          break;

        case 'conversation_stopped':
          shouldReconnectRef.current = false; // Don't reconnect when stopped
          setState(prev => ({
            ...prev,
            isComplete: true,
            currentAgentName: null,
          }));
          break;

        case 'paused':
          setState(prev => ({ ...prev, isPaused: true }));
          break;

        case 'resumed':
          setState(prev => ({ ...prev, isPaused: false }));
          break;

        case 'stopped':
          setState(prev => ({ ...prev, isComplete: true, isPaused: false }));
          break;

        case 'metadata':
          setState(prev => ({ ...prev, metadata: message.data }));
          break;

        case 'metadata_unavailable':
          console.log('Metadata not available:', message.message);
          break;

        case 'tool_use':
          // Agent is using a tool (e.g., fetching a URL)
          setState(prev => ({
            ...prev,
            currentToolUses: [...prev.currentToolUses, message.message || ''],
          }));
          break;

        case 'injected':
          // Content was successfully injected
          console.log('Content injected successfully:', message.message);
          // Optionally show a success notification here
          break;

        case 'error':
          setState(prev => ({ ...prev, error: message.message || 'Unknown error' }));
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Enable auto-reconnect for new connections
    shouldReconnectRef.current = true;

    const wsUrl = `${WS_URL}/ws/conversation/${conversationId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setState(prev => ({ ...prev, isConnected: true, error: null }));
    };

    ws.onmessage = handleMessage;

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setState(prev => ({ ...prev, error: 'Connection error' }));
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setState(prev => ({ ...prev, isConnected: false }));

      // Auto-reconnect after 3 seconds if we should reconnect
      // Use ref to avoid stale closure issues with state
      if (shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [conversationId, handleMessage]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false; // Don't reconnect on manual disconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Auto-connect removed - conversation page will call connect() manually when needed
  // This prevents auto-reconnection loops for viewing completed conversations

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    state,
    connect,
    disconnect,
    sendCommand,
    pause,
    resume,
    stop,
    requestMetadata,
    inject,
  };
}
