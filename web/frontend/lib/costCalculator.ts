/**
 * Cost Calculator - Calculate API costs based on token usage
 *
 * Mirrors the Python cost_calculator.py for frontend use
 * Uses Anthropic's official pricing (as of January 2025)
 * https://www.anthropic.com/pricing
 */

export interface ModelPricing {
  inputPrice: number;  // Per million tokens
  outputPrice: number; // Per million tokens
}

export interface CostBreakdown {
  inputCost: number;
  outputCost: number;
  totalCost: number;
  inputPricePerMTok: number;
  outputPricePerMTok: number;
}

export interface TokenStats {
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  thinkingTokens: number;
  totalCost: number;
}

/**
 * Anthropic pricing per million tokens (input, output)
 */
const ANTHROPIC_PRICING: Record<string, ModelPricing> = {
  // Claude 4.5 Models (Latest)
  'claude-sonnet-4-5-20250929': { inputPrice: 3.00, outputPrice: 15.00 },
  'claude-sonnet-4-20250514': { inputPrice: 3.00, outputPrice: 15.00 },

  // Claude 4 Models
  'claude-opus-4-20250514': { inputPrice: 15.00, outputPrice: 75.00 },

  // Claude 3.5 Models
  'claude-3-5-sonnet-20241022': { inputPrice: 3.00, outputPrice: 15.00 },
  'claude-3-5-sonnet-20240620': { inputPrice: 3.00, outputPrice: 15.00 },
  'claude-3-5-haiku-20241022': { inputPrice: 1.00, outputPrice: 5.00 },

  // Claude 3 Models (Legacy)
  'claude-3-opus-20240229': { inputPrice: 15.00, outputPrice: 75.00 },
  'claude-3-sonnet-20240229': { inputPrice: 3.00, outputPrice: 15.00 },
  'claude-3-haiku-20240307': { inputPrice: 0.25, outputPrice: 1.25 },

  // Default fallback (use Sonnet pricing)
  'default': { inputPrice: 3.00, outputPrice: 15.00 }
};

/**
 * Get pricing for a specific model
 */
export function getModelPricing(modelName: string): ModelPricing {
  return ANTHROPIC_PRICING[modelName] || ANTHROPIC_PRICING['default'];
}

/**
 * Calculate cost for a given number of tokens
 */
export function calculateCost(
  modelName: string,
  inputTokens: number,
  outputTokens: number
): CostBreakdown {
  const pricing = getModelPricing(modelName);

  // Calculate costs (price is per million tokens)
  const inputCost = (inputTokens / 1_000_000) * pricing.inputPrice;
  const outputCost = (outputTokens / 1_000_000) * pricing.outputPrice;
  const totalCost = inputCost + outputCost;

  return {
    inputCost,
    outputCost,
    totalCost,
    inputPricePerMTok: pricing.inputPrice,
    outputPricePerMTok: pricing.outputPrice
  };
}

/**
 * Get human-readable display name for a model
 */
export function getModelDisplayName(modelName: string): string {
  if (modelName.includes('opus-4')) {
    return 'Claude Opus 4 (Most Capable)';
  } else if (modelName.includes('sonnet-4-5') || modelName.includes('sonnet-4')) {
    return 'Claude Sonnet 4.5 (Balanced)';
  } else if (modelName.includes('sonnet-3-5')) {
    return 'Claude 3.5 Sonnet (Fast)';
  } else if (modelName.includes('haiku-3-5')) {
    return 'Claude 3.5 Haiku (Fastest)';
  } else if (modelName.includes('opus-3')) {
    return 'Claude 3 Opus (Legacy)';
  } else if (modelName.includes('sonnet-3')) {
    return 'Claude 3 Sonnet (Legacy)';
  } else if (modelName.includes('haiku-3')) {
    return 'Claude 3 Haiku (Legacy)';
  }
  return modelName;
}

/**
 * Calculate historical statistics from conversation exchanges
 *
 * This function aggregates token usage and calculates costs for completed conversations.
 * Note: Costs are calculated based on current model configuration, which may differ
 * from the models used when the conversation was originally created.
 */
export function calculateHistoricalStats(
  exchanges: Array<{ agent_name: string; tokens_used: number }>,
  agentAName: string,
  agentAModel: string,
  agentBName: string,
  agentBModel: string
): TokenStats & { perAgentStats: Record<string, { tokens: number; cost: number; model: string }> } {
  // Initialize aggregates
  let totalTokens = 0;
  let totalCost = 0;

  // Track per-agent stats
  const perAgentStats: Record<string, { tokens: number; cost: number; model: string }> = {
    [agentAName]: { tokens: 0, cost: 0, model: agentAModel },
    [agentBName]: { tokens: 0, cost: 0, model: agentBModel }
  };

  // Process each exchange
  for (const exchange of exchanges) {
    const tokens = exchange.tokens_used || 0;
    const agentName = exchange.agent_name;

    // Determine which model was used based on agent name
    const model = agentName === agentAName ? agentAModel : agentBModel;

    // Calculate cost for this exchange
    // Note: We're treating all tokens as output tokens for historical data
    // since we don't have input/output breakdown stored
    // This is a reasonable approximation since output tokens dominate the cost
    const costBreakdown = calculateCost(model, 0, tokens);
    const exchangeCost = costBreakdown.totalCost;

    // Update aggregates
    totalTokens += tokens;
    totalCost += exchangeCost;

    // Update per-agent stats
    if (perAgentStats[agentName]) {
      perAgentStats[agentName].tokens += tokens;
      perAgentStats[agentName].cost += exchangeCost;
    }
  }

  return {
    totalTokens,
    inputTokens: 0,  // Not available for historical data
    outputTokens: totalTokens,  // Treating all as output
    thinkingTokens: 0,  // Not tracked separately
    totalCost,
    perAgentStats
  };
}
