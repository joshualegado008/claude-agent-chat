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

// Prompt metadata - tracks the evolution of prompts through AI enhancements
export interface PromptMetadata {
  original_user_input: string;  // What the user originally typed
  generated_title?: string;      // AI-generated concise title (if different from original)
  generated_prompt?: string;     // AI-enhanced discussion prompt
  generated_tags?: string[];     // AI-suggested tags
  refined_topic?: string;        // Topic refined for agent selection (dynamic agents only)
  expertise_requirements?: string[];  // Expertise analysis (dynamic agents only)
  timestamps?: {
    title_generated_at?: string;
    prompt_generated_at?: string;
    topic_refined_at?: string;
  };
}

// Source/Citation for web research
export interface Source {
  source_id: string;
  title: string;
  url: string;
  publisher?: string;
  accessed_date?: string;
  excerpt?: string;
}

export interface Conversation {
  id: string;
  title: string;
  initial_prompt: string;
  prompt_metadata?: PromptMetadata;  // Prompt evolution metadata
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
  has_summary?: boolean;
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
  sources?: Source[];
  search_query?: string;  // Search query if autonomous search was triggered
  search_trigger_type?: string;  // Type of search trigger (fact_check, curiosity, etc.)
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
  | 'search_triggered'
  | 'search_complete'
  | 'summary_generation_start'
  | 'summary_generated'
  | 'summary_error'
  | 'summary_unavailable'
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
  // Search-related fields
  query?: string;
  trigger_type?: string;
  sources_count?: number;
  citations?: string[];
  search_query?: string;  // Included in turn_complete for persistence
  search_trigger_type?: string;  // Included in turn_complete for persistence
  sources?: Source[];  // Full source objects
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

// Conversation Summary Types (Post-Conversation Intelligence Report)

export interface KeyInsight {
  insight: string;
  significance: string;
  emerged_at_turn?: number;
}

export interface TechnicalTerm {
  term: string;
  definition: string;
  pronunciation?: string;
  context?: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

export interface VocabularyHighlight {
  word: string;
  definition: string;
  pronunciation?: string;
  usage_example?: string;
  why_interesting?: string;
}

export interface AgentContribution {
  agent_name: string;
  qualification: string;
  key_concepts: string[];
  technical_terms_introduced: string[];
  novel_insights: string[];
  sources_cited: string[];
  turn_count: number;
  engagement_level: 'high' | 'medium' | 'low';
  communication_style: string;
}

export interface CollaborativeMoment {
  turn_range: string;
  description: string;
}

export interface CollaborationDynamics {
  overall_quality: 'high' | 'medium' | 'low';
  interaction_pattern: 'agreement' | 'debate' | 'synthesis' | 'exploration';
  most_collaborative_moments: CollaborativeMoment[];
  points_of_convergence: string[];
  points_of_divergence: string[];
  friendliest_agent: string;
}

export interface NamedEntities {
  people: string[];
  organizations: string[];
  locations: string[];
  publications: string[];
  urls: string[];
}

export interface ConversationStats {
  total_turns: number;
  total_tokens: number;
  total_cost: number;
  combined_cost: number;
}

export interface GenerationMetadata {
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  generation_cost: number;
  generation_time_ms: number;
  generated_at: string;
  conversation_stats: ConversationStats;
  note?: string;
}

export interface SummaryData {
  tldr: string;
  executive_summary: string;
  key_insights: KeyInsight[];
  technical_glossary: TechnicalTerm[];
  vocabulary_highlights: VocabularyHighlight[];
  agent_contributions: AgentContribution[];
  collaboration_dynamics: CollaborationDynamics;
  named_entities: NamedEntities;
  learning_outcomes: string[];
  generation_metadata: GenerationMetadata;
}

export interface ConversationSummary {
  id: string;
  conversation_id: string;
  summary_data: SummaryData;
  generation_model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  generation_cost: number;
  generation_time_ms: number;
  generated_at: string;
}
