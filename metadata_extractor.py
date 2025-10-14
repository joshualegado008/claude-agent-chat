"""
Metadata Extractor - AI-powered rich metadata extraction for conversations
Uses OpenAI GPT-4o-mini for intelligent analysis
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import openai


class MetadataExtractor:
    """Extracts rich metadata from conversation titles and content."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: Optional OpenAI API key. If not provided, will check environment.
        """
        # Use provided key, or fall back to environment variable
        if api_key is None:
            api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Either pass it as a parameter or "
                "set OPENAI_API_KEY environment variable."
            )

        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def generate_initial_prompt(self, title: str) -> str:
        """
        Generate an engaging initial prompt from the conversation title.

        Args:
            title: The conversation title

        Returns:
            A well-crafted initial prompt for the agents
        """
        system_prompt = """You are a conversation starter expert. Given a topic/title,
create a thoughtful, engaging initial prompt that will spark an interesting discussion
between two AI agents. The prompt should:
- Be open-ended and thought-provoking
- Encourage multiple perspectives
- Be 2-3 sentences maximum
- Not just repeat the title"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {title}\n\nGenerate an initial prompt:"}
                ],
                max_tokens=150,
                temperature=0.8
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️  Failed to generate prompt: {e}")
            return f"Let's have a thoughtful discussion about: {title}"

    def extract_tags_from_title(self, title: str, max_tags: int = 5) -> List[str]:
        """
        Extract relevant tags from conversation title.

        Args:
            title: The conversation title
            max_tags: Maximum number of tags to extract

        Returns:
            List of extracted tags
        """
        system_prompt = """Extract relevant tags from the given topic.
Return a JSON object with a "tags" array.
Tags should be:
- Single words or short phrases (2-3 words max)
- Lowercase
- Relevant and descriptive
- Cover different aspects of the topic

Example: {"tags": ["philosophy", "self-reference", "recursion", "meaning"]}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {title}"}
                ],
                max_tokens=100,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            tags = result.get('tags', [])

            return tags[:max_tags]
        except Exception as e:
            print(f"⚠️  Failed to extract tags: {e}")
            # Fallback: simple keyword extraction
            words = title.lower().split()
            return [w for w in words if len(w) > 3][:max_tags]

    def analyze_conversation_snapshot(
        self,
        recent_exchanges: List[Dict],
        title: str,
        total_turns: int
    ) -> Dict:
        """
        Analyze current conversation state and extract rich metadata.

        Args:
            recent_exchanges: List of recent conversation exchanges
            title: Original conversation title
            total_turns: Total number of turns so far

        Returns:
            Dict containing rich metadata
        """
        # Build conversation context
        context = f"Title: {title}\nTotal turns: {total_turns}\n\nRecent exchanges:\n"
        for ex in recent_exchanges[-5:]:  # Last 5 exchanges
            agent = ex.get('agent_name', 'Unknown')
            content = ex.get('response_content', '')[:400]
            context += f"\n{agent}: {content}...\n"

        system_prompt = """Analyze this conversation and extract rich metadata.
Return a JSON object with this exact structure:
{
  "current_vibe": "brief description of current discussion atmosphere",
  "content_type": "reference/debate/exploration/analysis/creative/philosophical",
  "technical_level": "beginner/intermediate/advanced/expert",
  "sentiment": "positive/negative/neutral/mixed",
  "main_topics": ["topic1", "topic2", "topic3"],
  "key_concepts": ["concept1", "concept2", "concept3"],
  "named_entities": {
    "people": ["person1"],
    "organizations": ["org1"],
    "locations": ["loc1"],
    "technologies": ["tech1"]
  },
  "conversation_stage": "opening/exploration/deep_dive/debate/synthesis/conclusion",
  "complexity_level": 1-10 as integer,
  "engagement_quality": "high/medium/low",
  "emerging_themes": ["theme1", "theme2"]
}

Provide thoughtful analysis. If no entities found, use empty arrays."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=600,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            metadata = json.loads(response.choices[0].message.content)
            metadata['analyzed_at'] = datetime.now().isoformat()
            metadata['total_turns_analyzed'] = total_turns

            return metadata
        except Exception as e:
            print(f"⚠️  Failed to analyze conversation: {e}")
            return self._fallback_metadata(title, total_turns)

    async def refine_topic(self, raw_topic: str) -> str:
        """
        Refine raw user topic into a clear, engaging discussion question.

        Takes simple user input like "ancient canaanite eye diseases" and
        expands it into a clear discussion prompt like:
        "Explore ancient Canaanite beliefs about eye health, historical evidence
        of eye diseases, and modern medical understanding."

        Args:
            raw_topic: Raw user input (can be brief, informal)

        Returns:
            str: Refined, clear discussion question/prompt
        """
        system_prompt = """Refine the given topic into a clear, engaging discussion prompt.

The refined prompt should:
- Be 1-2 sentences
- Be clear and specific
- Encourage thoughtful multi-perspective discussion
- Expand on the original topic while staying focused
- Be appropriate for expert-level discussion

Examples:
Input: "photosynthesis"
Output: "Explore the biochemical processes of photosynthesis, its evolutionary development, and its role in Earth's ecosystems."

Input: "ancient canaanite eye diseases"
Output: "Discuss ancient Canaanite beliefs about eye health, historical evidence of eye diseases in the ancient Near East, and how modern ophthalmology interprets these historical accounts."

Input: "quantum computing"
Output: "Examine the principles of quantum computing, current technological challenges, and potential applications in cryptography and drug discovery."
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {raw_topic}"}
                ],
                max_tokens=150,
                temperature=0.7
            )

            refined = response.choices[0].message.content.strip()

            # Remove quotes if present
            if refined.startswith('"') and refined.endswith('"'):
                refined = refined[1:-1]

            return refined

        except Exception as e:
            print(f"⚠️  Failed to refine topic: {e}")
            # Fallback: Just capitalize and add context
            return f"Discuss {raw_topic} from multiple expert perspectives."

    async def analyze_expertise_requirements(self, topic: str) -> Dict:
        """
        Analyze topic and identify required expertise for dynamic agent selection.
        This is for Phase 1+ multi-agent system.

        Args:
            topic: Raw user topic/question

        Returns:
            Dict with:
                - refined_topic: str (clear discussion question)
                - expertise_needed: List[str] (specific expertise domains)
                - suggested_domains: List[str] (high-level domain names)
        """
        system_prompt = """Analyze this topic and identify expertise requirements for a multi-agent discussion.

Return a JSON object with this structure:
{
  "refined_topic": "Clear 1-2 sentence discussion question",
  "expertise_needed": ["Specific Expertise 1", "Specific Expertise 2", "Specific Expertise 3"],
  "suggested_domains": ["DOMAIN1", "DOMAIN2"]
}

For expertise_needed, provide 2-3 specific expert roles like:
- "Ancient Near Eastern History (Canaanite period)"
- "Ophthalmology (retinal diseases)"
- "Quantum Computing"

For suggested_domains, choose from:
SCIENCE, MEDICINE, HUMANITIES, TECHNOLOGY, BUSINESS, LAW, ARTS

Be specific and thoughtful."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {topic}"}
                ],
                max_tokens=300,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                'refined_topic': result.get('refined_topic', topic),
                'expertise_needed': result.get('expertise_needed', ["General Expert"]),
                'suggested_domains': result.get('suggested_domains', ["HUMANITIES"])
            }
        except Exception as e:
            print(f"⚠️  Failed to analyze expertise requirements: {e}")
            # Fallback
            return {
                'refined_topic': topic,
                'expertise_needed': ["General Expert"],
                'suggested_domains': ["HUMANITIES"]
            }

    def _fallback_metadata(self, title: str, total_turns: int) -> Dict:
        """Generate fallback metadata if AI analysis fails."""
        return {
            "current_vibe": "Engaging discussion in progress",
            "content_type": "exploration",
            "technical_level": "intermediate",
            "sentiment": "neutral",
            "main_topics": [title.lower()],
            "key_concepts": [],
            "named_entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "technologies": []
            },
            "conversation_stage": "exploration",
            "complexity_level": 5,
            "engagement_quality": "medium",
            "emerging_themes": [],
            "analyzed_at": datetime.now().isoformat(),
            "total_turns_analyzed": total_turns,
            "note": "Fallback metadata - AI analysis unavailable"
        }

    def extract_turn_insights(
        self,
        agent_name: str,
        response_content: str,
        thinking_content: Optional[str] = None
    ) -> Dict:
        """
        Extract quick insights from a single turn (lightweight).

        Args:
            agent_name: Name of the agent
            response_content: The agent's response
            thinking_content: Optional thinking content

        Returns:
            Dict with turn-level insights
        """
        # Lightweight extraction without API call
        word_count = len(response_content.split())

        # Simple sentiment heuristics
        positive_words = ['agree', 'excellent', 'great', 'love', 'wonderful', 'brilliant']
        negative_words = ['disagree', 'wrong', 'but', 'however', 'concern', 'worry']

        content_lower = response_content.lower()
        pos_count = sum(1 for w in positive_words if w in content_lower)
        neg_count = sum(1 for w in negative_words if w in content_lower)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "critical"
        else:
            sentiment = "neutral"

        # Check for questions
        has_question = '?' in response_content

        return {
            "agent": agent_name,
            "word_count": word_count,
            "sentiment": sentiment,
            "has_question": has_question,
            "has_thinking": thinking_content is not None,
            "timestamp": datetime.now().isoformat()
        }
