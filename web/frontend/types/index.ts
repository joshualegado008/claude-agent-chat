/**
 * Type definitions for Claude Agent Chat Web Interface
 */

// Agent info for multi-agent conversations
export interface AgentInfo {
  id: string;
  name: string;
  qualification?: string;
  model: string;
}

export interface Conversation {
  id: string;
  title: string;
  initial_prompt: string;
  // Legacy 2-agent fields (optional for backward compatibility)
  agent_a_id?: string;
  agent_a_name?: string;
  agent_a_qualification?: string;
  agent_a_model?: string;
  agent_b_id?: string;
  agent_b_name?: string;
  agent_b_qualification?: string;
  agent_b_model?: string;
  // New multi-agent field
  agents?: AgentInfo[];
  total_turns: number;
  total_tokens: number;
  status: 'active' | 'completed' | 'paused' | 'archived';
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
  | 'tool_use'
  | 'injected'
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

// Agent domain types
export type AgentDomain = 'science' | 'medicine' | 'humanities' | 'technology' | 'business' | 'law' | 'arts';

// Agent profile for dynamic agent selection
export interface AgentProfile {
  agent_id: string;
  name: string;
  domain: AgentDomain;
  domain_icon: string;
  primary_class: string;
  subclass: string;
  specialization: string;
  unique_expertise: string;
  core_skills: string[];
  keywords: string[];
  system_prompt: string;
  created_at: string;
  last_used: string;
  agent_file_path?: string | null;
  total_uses: number;
  creation_cost_usd: number;
  created_by: string;
  model: string;
  secondary_skills: string[];
}

// Agent selection metadata
export interface AgentSelectionMetadata {
  refined_topic: string;
  expertise_requirements: string[];
  agents_created: number;
  agents_reused: number;
  creation_cost: number;
  cache_savings: number;
}

// Agent selection response
export interface AgentSelectionResponse {
  agents: AgentProfile[];
  metadata: AgentSelectionMetadata;
}
