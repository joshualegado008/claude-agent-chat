"""
Agent Deduplication System

Prevents creating duplicate or overly similar agents by:
1. Detecting similarity using cosine similarity on embeddings
2. Enforcing capacity limits per agent class
3. Providing intelligent recommendations (reuse/suggest_reuse/create/deny)

Three-tier similarity thresholds:
- ≥95%: Definitely reuse existing agent
- 85-95%: Suggest reuse with unique angle option
- <85%: Allow creation (if capacity permits)
"""

from typing import List, Tuple, Optional, Dict
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.data_models import AgentProfile, AgentDomain


class AgentDeduplicationSystem:
    """Prevents duplicate agent creation through similarity analysis."""

    def __init__(self, taxonomy=None):
        """
        Initialize deduplication system.

        Args:
            taxonomy: AgentTaxonomy instance for classification and capacity checks
        """
        self.taxonomy = taxonomy
        self.active_agents: Dict[str, AgentProfile] = {}

        # Similarity thresholds
        self.REUSE_THRESHOLD = 0.95      # Definitely reuse
        self.SUGGEST_THRESHOLD = 0.85    # Suggest reuse with unique angle
        # Below 0.85: Allow creation

    def register_agent(self, agent: AgentProfile) -> None:
        """
        Register an agent in the deduplication system.

        Args:
            agent: AgentProfile to register
        """
        self.active_agents[agent.agent_id] = agent

        # Also register with taxonomy if available
        if self.taxonomy:
            self.taxonomy.add_agent(agent)

    def check_before_create(
        self,
        expertise_description: str,
        classification: Optional[Dict] = None,
        strict: bool = True
    ) -> Dict:
        """
        Check if agent should be created or reused.

        Process:
        1. Classify expertise (if not provided)
        2. Check class capacity
        3. Find similar agents using embedding similarity
        4. Make decision based on similarity and capacity

        Args:
            expertise_description: Description of required expertise
            classification: Optional pre-computed classification
            strict: If True, use strict thresholds (default)

        Returns:
            Decision dict with:
            - action: 'create' | 'reuse' | 'suggest_reuse' | 'deny'
            - reason: Why this decision was made
            - similar_agents: List of (agent, similarity) tuples
            - agent_id: ID to reuse (if action='reuse')
            - classification: Taxonomy classification
            - capacity_info: Class capacity info
            - unique_angle: Suggested unique angle (if suggest_reuse)
        """
        # Step 1: Classify expertise
        if not classification:
            if not self.taxonomy:
                # No taxonomy - can't check capacity or classify
                # Just check for exact duplicates
                return self._check_without_taxonomy(expertise_description)

            classification = self.taxonomy.classify_expertise(expertise_description)

            # Check if classification failed
            if not classification:
                return {
                    'action': 'create_with_warning',
                    'reason': f"Unable to classify '{expertise_description[:50]}...' into existing taxonomy. Will create with generic classification.",
                    'similar_agents': [],
                    'classification': None,
                    'capacity_info': {'at_capacity': False, 'count': 0, 'max': 10}
                }

        primary_class = classification['primary_class']
        domain = classification['domain']

        # Step 2: Check capacity
        capacity_info = {}
        if self.taxonomy:
            capacity_info = self.taxonomy.check_class_capacity(primary_class)
        else:
            capacity_info = {'at_capacity': False, 'count': 0, 'max': 10}

        # Step 3: Find similar agents
        threshold = self.SUGGEST_THRESHOLD if strict else (self.SUGGEST_THRESHOLD - 0.10)
        similar_agents = self._find_similar_agents(expertise_description, threshold)

        # Step 4: Decision logic
        if not similar_agents:
            # No similar agents found
            if capacity_info['at_capacity']:
                return {
                    'action': 'deny',
                    'reason': f"Class '{primary_class}' is at capacity ({capacity_info['count']}/{capacity_info['max']})",
                    'similar_agents': [],
                    'classification': classification,
                    'capacity_info': capacity_info
                }
            else:
                return {
                    'action': 'create',
                    'reason': f"No similar agents found. Capacity: {capacity_info['count']}/{capacity_info['max']}",
                    'similar_agents': [],
                    'classification': classification,
                    'capacity_info': capacity_info
                }

        # We have similar agents
        best_match, best_similarity = similar_agents[0]

        if best_similarity >= self.REUSE_THRESHOLD:
            # Very high similarity - definitely reuse
            return {
                'action': 'reuse',
                'reason': f"Existing agent '{best_match.name}' is {best_similarity*100:.1f}% similar (≥95% threshold)",
                'similar_agents': similar_agents[:3],
                'agent_id': best_match.agent_id,
                'classification': classification,
                'capacity_info': capacity_info
            }

        elif best_similarity >= self.SUGGEST_THRESHOLD:
            # Moderate similarity - suggest reuse but allow creation
            if capacity_info['at_capacity']:
                return {
                    'action': 'deny',
                    'reason': f"Similar agent exists ({best_similarity*100:.1f}% similar) and class is at capacity",
                    'similar_agents': similar_agents[:3],
                    'agent_id': best_match.agent_id,
                    'classification': classification,
                    'capacity_info': capacity_info
                }
            else:
                return {
                    'action': 'suggest_reuse',
                    'reason': f"Agent '{best_match.name}' is {best_similarity*100:.1f}% similar (85-95% range)",
                    'similar_agents': similar_agents[:3],
                    'agent_id': best_match.agent_id,
                    'classification': classification,
                    'capacity_info': capacity_info,
                    'unique_angle': self._suggest_unique_angle(expertise_description, best_match)
                }

        else:
            # Low similarity - allow creation if capacity permits
            if capacity_info['at_capacity']:
                return {
                    'action': 'deny',
                    'reason': f"Class '{primary_class}' is at capacity ({capacity_info['count']}/{capacity_info['max']})",
                    'similar_agents': similar_agents[:3],
                    'classification': classification,
                    'capacity_info': capacity_info
                }
            else:
                return {
                    'action': 'create',
                    'reason': f"Sufficiently different from existing agents ({best_similarity*100:.1f}% < 85%)",
                    'similar_agents': similar_agents[:3],
                    'classification': classification,
                    'capacity_info': capacity_info
                }

    def _find_similar_agents(
        self,
        expertise_description: str,
        threshold: float = 0.85
    ) -> List[Tuple[AgentProfile, float]]:
        """
        Find agents with similar expertise using embedding similarity.

        Args:
            expertise_description: Description to match against
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of (agent, similarity_score) tuples, sorted by similarity (descending)
        """
        if not self.active_agents:
            return []

        # Generate embedding for the query
        from src.agent_factory import AgentFactory
        factory = AgentFactory(taxonomy=None)  # Just need embedding function
        query_embedding = factory._generate_hash_embedding(expertise_description)

        similar = []
        for agent in self.active_agents.values():
            if agent.expertise_embedding is None:
                continue

            # Calculate cosine similarity
            similarity = self._calculate_similarity(query_embedding, agent.expertise_embedding)

            if similarity >= threshold:
                similar.append((agent, similarity))

        # Sort by similarity (descending)
        similar.sort(key=lambda x: x[1], reverse=True)

        return similar

    def _calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0-1.0)
        """
        # Reshape for sklearn
        emb1 = embedding1.reshape(1, -1)
        emb2 = embedding2.reshape(1, -1)

        # Calculate cosine similarity
        similarity = cosine_similarity(emb1, emb2)[0][0]

        # Ensure result is in [0, 1] range
        # (cosine similarity can be -1 to 1, but we want 0 to 1)
        return (similarity + 1) / 2

    def _suggest_unique_angle(
        self,
        new_expertise: str,
        existing_agent: AgentProfile
    ) -> str:
        """
        Suggest a unique angle to differentiate from existing agent.

        Args:
            new_expertise: Proposed new agent expertise
            existing_agent: Existing similar agent

        Returns:
            Suggestion string
        """
        existing_skills = ', '.join(list(existing_agent.core_skills)[:3])

        return (
            f"Consider reusing '{existing_agent.name}' who specializes in {existing_skills}. "
            f"If you need different expertise, specify how this differs (e.g., different "
            f"subspecialty, methodology, or application domain)."
        )

    def _check_without_taxonomy(self, expertise_description: str) -> Dict:
        """
        Simplified check when taxonomy is not available.

        Only checks for high-similarity duplicates.
        """
        similar_agents = self._find_similar_agents(expertise_description, self.REUSE_THRESHOLD)

        if similar_agents:
            best_match, best_similarity = similar_agents[0]
            return {
                'action': 'reuse',
                'reason': f"Existing agent is {best_similarity*100:.1f}% similar",
                'similar_agents': similar_agents[:3],
                'agent_id': best_match.agent_id,
                'classification': None,
                'capacity_info': {'at_capacity': False, 'count': 0, 'max': 10}
            }
        else:
            return {
                'action': 'create',
                'reason': 'No similar agents found',
                'similar_agents': [],
                'classification': None,
                'capacity_info': {'at_capacity': False, 'count': 0, 'max': 10}
            }

    def get_all_agents(self) -> List[AgentProfile]:
        """Get all registered agents."""
        return list(self.active_agents.values())

    def get_agent_count(self) -> int:
        """Get count of registered agents."""
        return len(self.active_agents)

    def get_agents_by_class(self, class_name: str) -> List[AgentProfile]:
        """Get all agents in a specific class."""
        return [
            agent for agent in self.active_agents.values()
            if agent.primary_class == class_name
        ]

    def clear(self) -> None:
        """Clear all registered agents (useful for testing)."""
        self.active_agents.clear()
