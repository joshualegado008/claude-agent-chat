/**
 * React Query hooks for conversation data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Conversation } from '@/types';

/**
 * Hook to fetch list of conversations
 */
export function useConversations(limit: number = 20) {
  return useQuery({
    queryKey: ['conversations', limit],
    queryFn: () => api.listConversations(limit),
  });
}

/**
 * Hook to fetch a single conversation
 */
export function useConversation(id: string) {
  return useQuery({
    queryKey: ['conversation', id],
    queryFn: () => api.getConversation(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      title: string;
      initial_prompt?: string;
      tags?: string[];
      generate_prompt?: boolean;
    }) => api.createConversation(data),
    onSuccess: () => {
      // Invalidate conversations list to refetch
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

/**
 * Hook to delete a conversation
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

/**
 * Hook to search conversations
 */
export function useSearchConversations(query: string, limit: number = 10) {
  return useQuery({
    queryKey: ['search', query, limit],
    queryFn: () => api.searchConversations(query, limit),
    enabled: query.length > 0,
  });
}

/**
 * Hook to generate prompt from title
 */
export function useGeneratePrompt() {
  return useMutation({
    mutationFn: (title: string) => api.generatePrompt(title),
  });
}
