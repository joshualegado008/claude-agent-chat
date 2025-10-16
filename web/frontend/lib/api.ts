/**
 * API Client - REST API calls to FastAPI backend
 */

import type { Conversation, SearchResult, AgentSelectionResponse } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(
      error.detail || 'API request failed',
      response.status,
      error
    );
  }
  return response.json();
}

export const api = {
  // Health check
  async healthCheck() {
    const response = await fetch(`${API_URL}/api/health`);
    return handleResponse(response);
  },

  // Conversations
  async listConversations(limit: number = 20): Promise<{ conversations: Conversation[]; count: number }> {
    const response = await fetch(`${API_URL}/api/conversations?limit=${limit}`);
    return handleResponse(response);
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await fetch(`${API_URL}/api/conversations/${id}`);
    return handleResponse(response);
  },

  async createConversation(data: {
    title: string;
    initial_prompt?: string;
    tags?: string[];
    generate_prompt?: boolean;
    agent_ids?: string[];
  }): Promise<{
    id: string;
    title: string;
    initial_prompt: string;
    tags: string[];
    message: string;
  }> {
    const response = await fetch(`${API_URL}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  async continueConversation(id: string, continuationPrompt?: string): Promise<{
    id: string;
    message: string;
    websocket_url: string;
  }> {
    const response = await fetch(`${API_URL}/api/conversations/${id}/continue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ continuation_prompt: continuationPrompt }),
    });
    return handleResponse(response);
  },

  async deleteConversation(id: string): Promise<{ message: string }> {
    const response = await fetch(`${API_URL}/api/conversations/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },

  // Search
  async searchConversations(query: string, limit: number = 10): Promise<{
    query: string;
    results: SearchResult[];
    count: number;
  }> {
    const response = await fetch(`${API_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit }),
    });
    return handleResponse(response);
  },

  // AI Generation
  async generatePrompt(title: string): Promise<{
    title: string;
    generated_prompt: string;
    suggested_tags: string[];
  }> {
    const response = await fetch(`${API_URL}/api/generate-prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    return handleResponse(response);
  },

  // Dynamic Agent Selection
  async selectAgents(topic: string): Promise<AgentSelectionResponse> {
    const response = await fetch(`${API_URL}/api/agents/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    });
    return handleResponse(response);
  },
};
