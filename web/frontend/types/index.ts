/**
 * Type definitions for Claude Agent Chat Web Interface
 */

export interface Conversation {
  id: string;
  title: string;
  initial_prompt: string;
  agent_a_name: string;
  agent_b_name: string;
  total_turns: number;
  total_tokens: number;
  status: 'active' | 'completed' | 'archived';
  tags: string[];
  created_at: string;
  updated_at: string;
  exchanges?: Exchange[];
}

export interface Exchange {
  turn_number: number;
  agent_name: string;
  thinking_content?: string | null;
  response_content: string;
  tokens_used: number;
  created_at: string;
}

export interface TokenStats {
  input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  total_tokens: number;
  turn_cost: number;
  total_cost: number;
  model_name: string;
  temperature: number;
  max_tokens: number;
  context_stats?: ContextStats;
  session_stats?: SessionStats;
}

export interface ContextStats {
  total_exchanges: number;
  window_size: number;
  context_chars: number;
  context_tokens_estimate: number;
  referenced_turns: number[];
}

export interface SessionStats {
  current_turn: number;
  max_turns: number;
  avg_tokens_per_turn: number;
  projected_total_tokens: number;
  projected_total_cost: number;
}

export interface ConversationMetadata {
  vibe?: string;
  sentiment?: {
    overall: string;
    score: number;
  };
  topics?: string[];
  entities?: {
    name: string;
    type: string;
    mentions: number;
  }[];
  complexity?: {
    level: string;
    score: number;
  };
  key_points?: string[];
  themes?: string[];
}

export interface SearchResult {
  id: string;
  title: string;
  turn_number: number;
  agent_name: string;
  response_content: string;
  similarity_score: number;
  created_at: string;
}

// WebSocket message types
export type WebSocketMessageType =
  | 'conversation_loaded'
  | 'ready'
  | 'turn_start'
  | 'thinking_start'
  | 'thinking_chunk'
  | 'response_chunk'
  | 'turn_complete'
  | 'conversation_complete'
  | 'conversation_stopped'
  | 'paused'
  | 'resumed'
  | 'stopped'
  | 'metadata'
  | 'metadata_unavailable'
  | 'error';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  turn?: number;
  agent_name?: string;
  agent_id?: string;
  chunk?: string;
  response?: string;
  thinking?: string;
  stats?: TokenStats;
  data?: any;
  message?: string;
  total_turns?: number;
  total_tokens?: number;
  total_cost?: number;
}

// WebSocket command types
export type WebSocketCommand = 'pause' | 'resume' | 'stop' | 'get_metadata';

export interface WebSocketCommandMessage {
  command: WebSocketCommand;
}
