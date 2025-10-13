/**
 * Utility functions
 */

import { type ClassValue, clsx } from 'clsx';

/**
 * Merge class names using clsx
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Format cost as currency
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${cost.toFixed(4)}`;
  } else if (cost < 1) {
    return `$${cost.toFixed(3)}`;
  } else {
    return `$${cost.toFixed(2)}`;
  }
}

/**
 * Format large numbers with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Format date relative to now (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = typeof date === 'string' ? new Date(date) : date;
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return then.toLocaleDateString();
}

/**
 * Get agent color based on agent name
 */
export function getAgentColor(agentName: string): string {
  if (agentName.toLowerCase().includes('nova')) {
    return 'nova'; // cyan
  } else if (agentName.toLowerCase().includes('atlas')) {
    return 'atlas'; // yellow
  }
  return 'gray';
}

/**
 * Get sentiment emoji
 */
export function getSentimentEmoji(sentiment: string): string {
  const lower = sentiment.toLowerCase();
  if (lower.includes('positive') || lower.includes('optimistic')) return '😊';
  if (lower.includes('negative') || lower.includes('pessimistic')) return '😟';
  if (lower.includes('neutral')) return '😐';
  if (lower.includes('curious')) return '🤔';
  if (lower.includes('excited')) return '🤩';
  return '💬';
}

/**
 * Get complexity color
 */
export function getComplexityColor(level: string): string {
  const lower = level.toLowerCase();
  if (lower.includes('low') || lower.includes('simple')) return 'green';
  if (lower.includes('medium') || lower.includes('moderate')) return 'yellow';
  if (lower.includes('high') || lower.includes('complex')) return 'red';
  return 'gray';
}

/**
 * Truncate text to specified length
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}
