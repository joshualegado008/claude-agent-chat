"""
Conversation Summarizer - Post-Conversation Intelligence Report Generator
Uses OpenAI GPT-4o-mini to generate comprehensive conversation summaries
"""

import os
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
import openai


class ConversationSummarizer:
    """
    Generates comprehensive intelligence reports for completed conversations.

    Features:
    - TL;DR (ultra-brief summary)
    - Executive Summary
    - Key Insights & Emergent Ideas
    - Technical Glossary with pronunciations
    - Vocabulary Highlights
    - Agent Contribution Analysis
    - Collaboration Dynamics
    - Named Entities & References
    - Learning Outcomes
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client for summary generation.

        Args:
            api_key: Optional OpenAI API key. Falls back to environment variable.
        """
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Either pass it as a parameter or "
                "set OPENAI_API_KEY environment variable."
            )

        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

        # Pricing for gpt-4o-mini (as of 2025)
        # https://openai.com/api/pricing/
        self.price_per_1k_input = 0.000150  # $0.15 per 1M input tokens
        self.price_per_1k_output = 0.000600  # $0.60 per 1M output tokens

    def generate_summary(
        self,
        conversation_title: str,
        initial_prompt: str,
        exchanges: List[Dict],
        agents: List[Dict],
        total_turns: int,
        total_tokens: int,
        total_cost: float
    ) -> Dict:
        """
        Generate comprehensive conversation summary.

        Args:
            conversation_title: Title of the conversation
            initial_prompt: Original prompt that started the conversation
            exchanges: List of exchange dicts with agent_name, response_content, etc.
            agents: List of agent dicts with id, name, qualification
            total_turns: Total number of turns in conversation
            total_tokens: Total tokens used in conversation
            total_cost: Total cost of conversation

        Returns:
            Dict containing:
                - summary_data: Full structured summary
                - tokens_used: Tokens used for summary generation
                - generation_cost: Cost of generating summary
                - generation_time_ms: Time taken to generate
        """
        start_time = time.time()

        # Build conversation context for analysis
        context = self._build_context(
            conversation_title,
            initial_prompt,
            exchanges,
            agents,
            total_turns
        )

        # Generate the comprehensive summary
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": context}
                ],
                max_tokens=4000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Extract response
            summary_json = response.choices[0].message.content
            summary_data = json.loads(summary_json)

            # Calculate costs
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            tokens_used = input_tokens + output_tokens

            generation_cost = (
                (input_tokens / 1000) * self.price_per_1k_input +
                (output_tokens / 1000) * self.price_per_1k_output
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Add metadata to summary
            summary_data['generation_metadata'] = {
                'model': self.model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': tokens_used,
                'generation_cost': generation_cost,
                'generation_time_ms': generation_time_ms,
                'generated_at': datetime.now().isoformat(),
                'conversation_stats': {
                    'total_turns': total_turns,
                    'total_tokens': total_tokens,
                    'total_cost': total_cost,
                    'combined_cost': total_cost + generation_cost
                }
            }

            return {
                'summary_data': summary_data,
                'model': self.model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': tokens_used,
                'cost': generation_cost,
                'generation_time_ms': generation_time_ms
            }

        except Exception as e:
            print(f"❌ Failed to generate summary: {e}")
            # Return fallback summary
            return self._fallback_summary(
                conversation_title,
                total_turns,
                agents,
                0,
                0.0,
                int((time.time() - start_time) * 1000)
            )

    def _build_context(
        self,
        title: str,
        initial_prompt: str,
        exchanges: List[Dict],
        agents: List[Dict],
        total_turns: int
    ) -> str:
        """Build context string for the AI to analyze."""

        # Agent information
        agent_info = "\n".join([
            f"- {agent.get('name')} ({agent.get('qualification', 'General Expert')})"
            for agent in agents
        ])

        # Conversation exchanges (all of them for comprehensive analysis)
        exchange_text = ""
        for idx, ex in enumerate(exchanges):
            agent_name = ex.get('agent_name', 'Unknown')
            content = ex.get('response_content', '')
            sources = ex.get('sources', [])

            exchange_text += f"\n\n--- Turn {idx} - {agent_name} ---\n{content}"

            # Include sources/citations if present
            if sources and len(sources) > 0:
                exchange_text += "\n\n[SOURCES CITED:]"
                for source in sources:
                    title = source.get('title', 'Unknown')
                    url = source.get('url', '')
                    publisher = source.get('publisher', '')
                    exchange_text += f"\n- {title}"
                    if publisher:
                        exchange_text += f" ({publisher})"
                    if url:
                        exchange_text += f" - {url}"

        context = f"""Analyze this complete expert conversation and generate a comprehensive intelligence report.

CONVERSATION METADATA:
Title: {title}
Initial Prompt: {initial_prompt}
Total Turns: {total_turns}
Agents:
{agent_info}

FULL CONVERSATION:
{exchange_text}

Generate a comprehensive analysis following the JSON structure provided in the system prompt."""

        return context

    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the summary structure."""
        return """You are an expert conversation analyst. Generate a comprehensive Post-Conversation Intelligence Report in JSON format.

Your output MUST be valid JSON with this EXACT structure:

{
  "tldr": "1-2 sentence ultra-brief summary of the entire conversation",

  "executive_summary": "1 paragraph comprehensive overview of main topics, perspectives, and conclusions",

  "key_insights": [
    {
      "insight": "Description of novel concept or breakthrough idea",
      "significance": "Why this insight is important or novel",
      "emerged_at_turn": 5
    }
  ],

  "technical_glossary": [
    {
      "term": "Technical or scientific term",
      "definition": "Clear, accessible definition",
      "pronunciation": "foh-NEH-tik pronunciation (if complex)",
      "context": "How it was used in the conversation",
      "difficulty": "beginner|intermediate|advanced"
    }
  ],

  "vocabulary_highlights": [
    {
      "word": "Interesting vocabulary word",
      "definition": "Definition",
      "pronunciation": "pronunciation guide",
      "usage_example": "Example from conversation",
      "why_interesting": "Etymology, rarity, or educational value"
    }
  ],

  "agent_contributions": [
    {
      "agent_name": "Agent Name",
      "qualification": "Their expertise",
      "key_concepts": ["concept1", "concept2"],
      "technical_terms_introduced": ["term1", "term2"],
      "novel_insights": ["insight1"],
      "sources_cited": ["Title of source 1", "Title of source 2"],
      "turn_count": 10,
      "engagement_level": "high|medium|low",
      "communication_style": "Brief description of their approach"
    }
  ],

  "collaboration_dynamics": {
    "overall_quality": "high|medium|low",
    "interaction_pattern": "agreement|debate|synthesis|exploration",
    "most_collaborative_moments": [
      {
        "turn_range": "5-7",
        "description": "What made this collaborative"
      }
    ],
    "points_of_convergence": ["topic where agents agreed"],
    "points_of_divergence": ["topic where agents disagreed"],
    "friendliest_agent": "Agent who was most collaborative and supportive"
  },

  "named_entities": {
    "people": ["Person names mentioned"],
    "organizations": ["Organizations mentioned"],
    "locations": ["Places mentioned"],
    "publications": ["Papers, books, articles cited"],
    "urls": ["URLs or websites referenced"]
  },

  "learning_outcomes": [
    "What readers can learn from this conversation",
    "Key takeaways for education or understanding"
  ]
}

IMPORTANT GUIDELINES:
1. **Key Insights**: Focus on ideas that EMERGED during conversation, not just topics from the initial prompt
2. **Technical Glossary**: Include medical, scientific, technical, or domain-specific terms that are difficult to understand
3. **Vocabulary Highlights**: Choose 3-5 interesting words that expand vocabulary - focus on sophisticated or uncommon words
4. **Pronunciation**: Provide phonetic guides for difficult words (e.g., "pseudopseudohypoparathyroidism" → "SOO-doh-SOO-doh-HY-poh-pa-ra-THY-royd-izm")
5. **Agent Contributions**: Be specific about what each agent uniquely contributed
6. **Sources Cited**: Extract the titles of all sources/citations used by each agent (look for [SOURCES CITED:] sections in turns)
7. **Collaboration**: Identify the friendliest/most supportive agent based on their language and interaction style
8. **Learning Outcomes**: Focus on what makes this conversation educational or valuable

Return ONLY valid JSON, no other text."""

    def _fallback_summary(
        self,
        title: str,
        total_turns: int,
        agents: List[Dict],
        tokens_used: int,
        generation_cost: float,
        generation_time_ms: int
    ) -> Dict:
        """Generate a minimal fallback summary if AI analysis fails."""
        agent_names = [agent.get('name', 'Unknown') for agent in agents]

        summary_data = {
            "tldr": f"A {total_turns}-turn conversation between {', '.join(agent_names)} about {title}.",
            "executive_summary": f"This conversation explored {title} through {total_turns} exchanges between {len(agents)} expert agents.",
            "key_insights": [],
            "technical_glossary": [],
            "vocabulary_highlights": [],
            "agent_contributions": [
                {
                    "agent_name": agent.get('name'),
                    "qualification": agent.get('qualification', 'General Expert'),
                    "key_concepts": [],
                    "technical_terms_introduced": [],
                    "novel_insights": [],
                    "sources_cited": [],
                    "turn_count": 0,
                    "engagement_level": "unknown",
                    "communication_style": "Unknown"
                }
                for agent in agents
            ],
            "collaboration_dynamics": {
                "overall_quality": "unknown",
                "interaction_pattern": "unknown",
                "most_collaborative_moments": [],
                "points_of_convergence": [],
                "points_of_divergence": [],
                "friendliest_agent": "Unknown"
            },
            "named_entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "publications": [],
                "urls": []
            },
            "learning_outcomes": [
                "Summary generation failed - fallback data provided"
            ],
            "generation_metadata": {
                "model": self.model,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": tokens_used,
                "generation_cost": generation_cost,
                "generation_time_ms": generation_time_ms,
                "generated_at": datetime.now().isoformat(),
                "note": "Fallback summary - AI analysis unavailable"
            }
        }

        return {
            'summary_data': summary_data,
            'model': self.model,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': tokens_used,
            'cost': generation_cost,
            'generation_time_ms': generation_time_ms
        }
