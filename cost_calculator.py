"""
Cost Calculator - Calculate API costs based on token usage

Uses Anthropic's official pricing (as of January 2025):
https://www.anthropic.com/pricing

Pricing per million tokens (MTok):
"""

from typing import Dict, Tuple


class CostCalculator:
    """Calculate costs for Anthropic API usage based on token counts."""

    # Anthropic pricing per million tokens (input, output)
    # Format: model_name: (input_price_per_mtok, output_price_per_mtok)
    ANTHROPIC_PRICING = {
        # Claude 4.5 Models (Latest)
        'claude-sonnet-4-5-20250929': (3.00, 15.00),
        'claude-sonnet-4-20250514': (3.00, 15.00),

        # Claude 4 Models
        'claude-opus-4-20250514': (15.00, 75.00),

        # Claude 3.5 Models
        'claude-3-5-sonnet-20241022': (3.00, 15.00),
        'claude-3-5-sonnet-20240620': (3.00, 15.00),
        'claude-3-5-haiku-20241022': (1.00, 5.00),

        # Claude 3 Models (Legacy)
        'claude-3-opus-20240229': (15.00, 75.00),
        'claude-3-sonnet-20240229': (3.00, 15.00),
        'claude-3-haiku-20240307': (0.25, 1.25),

        # Default fallback (use Sonnet pricing)
        'default': (3.00, 15.00)
    }

    # OpenAI Embedding pricing (for context embeddings)
    # text-embedding-3-small: $0.02 per MTok
    # text-embedding-3-large: $0.13 per MTok
    OPENAI_EMBEDDING_PRICING = {
        'text-embedding-3-small': 0.02,
        'text-embedding-3-large': 0.13,
        'text-embedding-ada-002': 0.10,
        'default': 0.02
    }

    @classmethod
    def get_model_pricing(cls, model_name: str) -> Tuple[float, float]:
        """
        Get pricing for a specific model.

        Args:
            model_name: The model identifier

        Returns:
            Tuple of (input_price_per_mtok, output_price_per_mtok)
        """
        return cls.ANTHROPIC_PRICING.get(model_name, cls.ANTHROPIC_PRICING['default'])

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Calculate cost for a given number of tokens.

        Args:
            model_name: The model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary with detailed cost breakdown:
            {
                'input_cost': float,
                'output_cost': float,
                'total_cost': float,
                'input_price_per_mtok': float,
                'output_price_per_mtok': float
            }
        """
        input_price, output_price = cls.get_model_pricing(model_name)

        # Calculate costs (price is per million tokens)
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        total_cost = input_cost + output_cost

        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'input_price_per_mtok': input_price,
            'output_price_per_mtok': output_price
        }

    @classmethod
    def calculate_embedding_cost(
        cls,
        model_name: str,
        tokens: int
    ) -> float:
        """
        Calculate cost for embedding generation.

        Args:
            model_name: The embedding model identifier
            tokens: Number of tokens

        Returns:
            Cost in dollars
        """
        price = cls.OPENAI_EMBEDDING_PRICING.get(
            model_name,
            cls.OPENAI_EMBEDDING_PRICING['default']
        )

        return (tokens / 1_000_000) * price

    @classmethod
    def format_cost(cls, cost: float) -> str:
        """
        Format a cost value for display.

        Args:
            cost: Cost in dollars

        Returns:
            Formatted string (e.g., "$0.0123" or "$1.23")
        """
        if cost < 0.01:
            # Show 4 decimal places for very small costs
            return f"${cost:.4f}"
        elif cost < 1.0:
            # Show 3 decimal places for costs under $1
            return f"${cost:.3f}"
        else:
            # Show 2 decimal places for larger costs
            return f"${cost:.2f}"

    @classmethod
    def get_available_models(cls) -> list:
        """
        Get list of available Anthropic models.

        Returns:
            List of model names with their pricing info
        """
        models = []
        for model_name, (input_price, output_price) in cls.ANTHROPIC_PRICING.items():
            if model_name == 'default':
                continue

            models.append({
                'name': model_name,
                'display_name': cls._get_display_name(model_name),
                'input_price': input_price,
                'output_price': output_price
            })

        return models

    @classmethod
    def _get_display_name(cls, model_name: str) -> str:
        """Convert model name to human-readable display name."""
        # Extract key parts
        if 'opus-4' in model_name:
            return "Claude Opus 4 (Most Capable)"
        elif 'sonnet-4-5' in model_name or 'sonnet-4' in model_name:
            return "Claude Sonnet 4.5 (Balanced)"
        elif 'sonnet-3-5' in model_name:
            return "Claude 3.5 Sonnet (Fast)"
        elif 'haiku-3-5' in model_name:
            return "Claude 3.5 Haiku (Fastest)"
        elif 'opus-3' in model_name:
            return "Claude 3 Opus (Legacy)"
        elif 'sonnet-3' in model_name:
            return "Claude 3 Sonnet (Legacy)"
        elif 'haiku-3' in model_name:
            return "Claude 3 Haiku (Legacy)"
        else:
            return model_name

    @classmethod
    def get_model_by_display_name(cls, display_name: str) -> str:
        """Get model identifier from display name."""
        for model in cls.get_available_models():
            if model['display_name'] == display_name:
                return model['name']
        return 'claude-sonnet-4-5-20250929'  # Default


# Convenience functions for quick calculations

def calculate_turn_cost(model_name: str, input_tokens: int, output_tokens: int) -> str:
    """Calculate and format cost for a single turn."""
    result = CostCalculator.calculate_cost(model_name, input_tokens, output_tokens)
    return CostCalculator.format_cost(result['total_cost'])


def calculate_session_cost(turns: list) -> Dict[str, any]:
    """
    Calculate total cost for a session with multiple turns.

    Args:
        turns: List of dicts with 'model', 'input_tokens', 'output_tokens'

    Returns:
        Dictionary with total tokens, total cost, and per-model breakdown
    """
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0
    model_costs = {}

    for turn in turns:
        model = turn.get('model', 'default')
        input_tokens = turn.get('input_tokens', 0)
        output_tokens = turn.get('output_tokens', 0)

        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        result = CostCalculator.calculate_cost(model, input_tokens, output_tokens)
        turn_cost = result['total_cost']
        total_cost += turn_cost

        # Track per-model costs
        if model not in model_costs:
            model_costs[model] = {
                'input_tokens': 0,
                'output_tokens': 0,
                'cost': 0.0
            }

        model_costs[model]['input_tokens'] += input_tokens
        model_costs[model]['output_tokens'] += output_tokens
        model_costs[model]['cost'] += turn_cost

    return {
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'total_tokens': total_input_tokens + total_output_tokens,
        'total_cost': total_cost,
        'formatted_cost': CostCalculator.format_cost(total_cost),
        'model_breakdown': model_costs
    }
