"""
Core data models for dynamic multi-agent system.

This module defines the data structures used throughout Phase 1:
- AgentProfile: Complete agent profile with taxonomy and expertise
- AgentDomain/Tier/Rank: Enums for classification and lifecycle
- ConversationRating: Performance ratings for agents
- AgentPerformanceProfile: Complete performance history with promotions
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Set, Dict, Optional
import numpy as np


class AgentDomain(Enum):
    """Top-level expertise domains."""
    SCIENCE = "science"
    MEDICINE = "medicine"
    HUMANITIES = "humanities"
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    LAW = "law"
    ARTS = "arts"

    @property
    def icon(self):
        """Visual icon for domain."""
        icons = {
            AgentDomain.SCIENCE: "🔬",
            AgentDomain.MEDICINE: "⚕️",
            AgentDomain.HUMANITIES: "📚",
            AgentDomain.TECHNOLOGY: "💻",
            AgentDomain.BUSINESS: "💼",
            AgentDomain.LAW: "⚖️",
            AgentDomain.ARTS: "🎨"
        }
        return icons.get(self, "🤖")


class AgentTier(Enum):
    """Agent lifecycle tiers based on usage."""
    HOT = "hot"          # Currently active in conversation
    WARM = "warm"        # Used within 7 days (instant retrieval)
    COLD = "cold"        # Used 7-90 days ago (slower retrieval)
    ARCHIVED = "archived" # 90+ days, candidate for retirement
    RETIRED = "retired"   # Deleted, pattern saved


class AgentRank(Enum):
    """Agent promotion ranks based on performance."""
    NOVICE = 1        # 0-9 points (new agents)
    COMPETENT = 2     # 10-24 points
    EXPERT = 3        # 25-49 points
    MASTER = 4        # 50-99 points
    LEGENDARY = 5     # 100-199 points
    GOD_TIER = 6      # 200+ points (never retired)


@dataclass
class AgentProfile:
    """Complete agent profile with expertise and metadata."""

    # Identity
    agent_id: str
    name: str

    # Taxonomy
    domain: AgentDomain
    primary_class: str
    subclass: str
    specialization: str

    # Expertise
    unique_expertise: str
    core_skills: List[str]
    keywords: Set[str]

    # System
    system_prompt: str
    created_at: datetime
    last_used: datetime

    # Phase 1C: Additional fields for dynamic agent creation
    agent_file_path: Optional[str] = None
    total_uses: int = 0
    creation_cost_usd: float = 0.0
    created_by: str = "system"
    model: str = "claude-sonnet-4-5"
    secondary_skills: List[str] = field(default_factory=list)

    # Embeddings (for similarity detection)
    expertise_embedding: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        data = {
            'agent_id': self.agent_id,
            'name': self.name,
            'domain': self.domain.value,
            'primary_class': self.primary_class,
            'subclass': self.subclass,
            'specialization': self.specialization,
            'unique_expertise': self.unique_expertise,
            'core_skills': self.core_skills,
            'keywords': list(self.keywords),
            'system_prompt': self.system_prompt,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat(),
            # Phase 1C fields
            'agent_file_path': self.agent_file_path,
            'total_uses': self.total_uses,
            'creation_cost_usd': self.creation_cost_usd,
            'created_by': self.created_by,
            'model': self.model,
            'secondary_skills': self.secondary_skills
        }
        # Handle numpy array separately
        if self.expertise_embedding is not None:
            data['expertise_embedding'] = self.expertise_embedding.tolist()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentProfile':
        """Create from dict."""
        # Handle embedding if present
        embedding = None
        if 'expertise_embedding' in data and data['expertise_embedding']:
            embedding = np.array(data['expertise_embedding'])

        return cls(
            agent_id=data['agent_id'],
            name=data['name'],
            domain=AgentDomain(data['domain']),
            primary_class=data['primary_class'],
            subclass=data['subclass'],
            specialization=data['specialization'],
            unique_expertise=data['unique_expertise'],
            core_skills=data['core_skills'],
            keywords=set(data['keywords']),
            system_prompt=data['system_prompt'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_used=datetime.fromisoformat(data['last_used']),
            # Phase 1C fields (with defaults for backward compatibility)
            agent_file_path=data.get('agent_file_path'),
            total_uses=data.get('total_uses', 0),
            creation_cost_usd=data.get('creation_cost_usd', 0.0),
            created_by=data.get('created_by', 'system'),
            model=data.get('model', 'claude-sonnet-4-5'),
            secondary_skills=data.get('secondary_skills', []),
            expertise_embedding=embedding
        )

    def display_card(self) -> str:
        """Beautiful terminal display card with box drawing."""
        # Truncate long strings for display
        name_display = self.name[:50]
        domain_display = self.domain.value
        class_display = self.primary_class
        spec_display = self.specialization[:43] if len(self.specialization) > 43 else self.specialization
        expertise_display = self.unique_expertise[:46] if len(self.unique_expertise) > 46 else self.unique_expertise
        skills_display = ', '.join(self.core_skills[:3])
        if len(skills_display) > 48:
            skills_display = skills_display[:45] + '...'
        created_display = self.created_at.strftime('%Y-%m-%d %H:%M')

        return f"""╔══════════════════════════════════════════════════════════╗
║ {self.domain.icon} {name_display:<50} ║
╠══════════════════════════════════════════════════════════╣
║ Domain: {domain_display:<48} ║
║ Class: {class_display:<49} ║
║ Specialization: {spec_display:<43} ║
║                                                          ║
║ Expertise: {expertise_display:<46} ║
║ Skills: {skills_display:<48} ║
║                                                          ║
║ Created: {created_display:<46} ║
║ Uses: {self.total_uses:<52} ║
╚══════════════════════════════════════════════════════════╝"""


@dataclass
class ConversationRating:
    """Rating for an agent's performance in a conversation."""

    agent_id: str
    conversation_id: str
    timestamp: datetime

    # Human ratings (1-5 scale)
    helpfulness: int
    accuracy: int
    relevance: int
    clarity: int
    collaboration: int

    # Computed
    overall_score: float  # Weighted average
    quality_points: int   # For promotions (0-5 based on overall)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'agent_id': self.agent_id,
            'conversation_id': self.conversation_id,
            'timestamp': self.timestamp.isoformat(),
            'helpfulness': self.helpfulness,
            'accuracy': self.accuracy,
            'relevance': self.relevance,
            'clarity': self.clarity,
            'collaboration': self.collaboration,
            'overall_score': self.overall_score,
            'quality_points': self.quality_points
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConversationRating':
        """Create from dict."""
        return cls(
            agent_id=data['agent_id'],
            conversation_id=data['conversation_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            helpfulness=data['helpfulness'],
            accuracy=data['accuracy'],
            relevance=data['relevance'],
            clarity=data['clarity'],
            collaboration=data['collaboration'],
            overall_score=data['overall_score'],
            quality_points=data['quality_points']
        )


@dataclass
class AgentPerformanceProfile:
    """Complete performance history for an agent."""

    agent_id: str
    agent_name: str
    total_conversations: int = 0
    total_points: int = 0
    current_rank: AgentRank = AgentRank.NOVICE
    average_score: float = 0.0
    ratings: List[ConversationRating] = field(default_factory=list)

    def add_rating(self, rating: ConversationRating):
        """Add rating and update stats."""
        self.ratings.append(rating)
        self.total_conversations += 1
        self.total_points += rating.quality_points
        self._recalculate_average()
        self._check_promotion()

    def _recalculate_average(self):
        """Recalculate average score."""
        if self.ratings:
            self.average_score = sum(r.overall_score for r in self.ratings) / len(self.ratings)

    def _check_promotion(self):
        """Check if agent should be promoted."""
        if self.total_points >= 200:
            self.current_rank = AgentRank.GOD_TIER
        elif self.total_points >= 100:
            self.current_rank = AgentRank.LEGENDARY
        elif self.total_points >= 50:
            self.current_rank = AgentRank.MASTER
        elif self.total_points >= 25:
            self.current_rank = AgentRank.EXPERT
        elif self.total_points >= 10:
            self.current_rank = AgentRank.COMPETENT
        else:
            self.current_rank = AgentRank.NOVICE

    def should_retire(self, days_unused: int) -> bool:
        """Determine if agent should be retired."""
        # God tier never retires
        if self.current_rank == AgentRank.GOD_TIER:
            return False

        # Novice agents retire after 6 months unused
        if self.current_rank == AgentRank.NOVICE and days_unused > 180:
            return True

        # Other ranks have longer grace periods
        if self.current_rank == AgentRank.COMPETENT and days_unused > 365:
            return True

        return False
