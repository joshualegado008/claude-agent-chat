"""
Rating System - Agent performance tracking, ratings, and promotions

This module implements:
- Multi-dimensional conversation ratings (5 dimensions)
- Agent rank system (NOVICE through GOD_TIER)
- Promotion logic based on performance points
- Performance profile tracking
- Leaderboard generation

Agents are rated on 5 dimensions (1-5 scale):
- Helpfulness (30% weight)
- Accuracy (25% weight)
- Relevance (20% weight)
- Clarity (15% weight)
- Collaboration (10% weight)

Promotion ranks:
- NOVICE: 0-9 points
- COMPETENT: 10-24 points
- EXPERT: 25-49 points
- MASTER: 50-99 points
- LEGENDARY: 100-199 points
- GOD_TIER: 200+ points (never retired)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple
import yaml


class AgentRank(Enum):
    """Agent promotion ranks based on performance points."""

    NOVICE = 1        # 0-9 points (new agents)
    COMPETENT = 2     # 10-24 points
    EXPERT = 3        # 25-49 points
    MASTER = 4        # 50-99 points
    LEGENDARY = 5     # 100-199 points
    GOD_TIER = 6      # 200+ points (never retired)

    @property
    def icon(self) -> str:
        """Visual icon for rank."""
        icons = {
            AgentRank.NOVICE: "📗",
            AgentRank.COMPETENT: "📘",
            AgentRank.EXPERT: "🔷",
            AgentRank.MASTER: "💎",
            AgentRank.LEGENDARY: "⭐",
            AgentRank.GOD_TIER: "🌟"
        }
        return icons[self]

    @property
    def min_points(self) -> int:
        """Minimum points required for this rank."""
        thresholds = {
            AgentRank.NOVICE: 0,
            AgentRank.COMPETENT: 10,
            AgentRank.EXPERT: 25,
            AgentRank.MASTER: 50,
            AgentRank.LEGENDARY: 100,
            AgentRank.GOD_TIER: 200
        }
        return thresholds[self]

    @property
    def retirement_protection_days(self) -> int:
        """Days of protection from retirement when unused."""
        protection = {
            AgentRank.NOVICE: 7,
            AgentRank.COMPETENT: 30,
            AgentRank.EXPERT: 90,
            AgentRank.MASTER: 180,
            AgentRank.LEGENDARY: 365,
            AgentRank.GOD_TIER: 99999  # Never
        }
        return protection[self]

    @property
    def display_name(self) -> str:
        """Human-readable rank name."""
        return self.name.replace('_', ' ').title()

    @classmethod
    def from_points(cls, points: int) -> 'AgentRank':
        """Determine rank from promotion points."""
        if points >= 200:
            return cls.GOD_TIER
        elif points >= 100:
            return cls.LEGENDARY
        elif points >= 50:
            return cls.MASTER
        elif points >= 25:
            return cls.EXPERT
        elif points >= 10:
            return cls.COMPETENT
        else:
            return cls.NOVICE


@dataclass
class ConversationRating:
    """Rating for an agent's performance in a conversation."""

    agent_id: str
    conversation_id: str
    timestamp: datetime

    # Human ratings (1-5 scale)
    helpfulness: int        # How helpful was this agent?
    accuracy: int           # How accurate was the information?
    relevance: int          # How relevant to the discussion?
    clarity: int            # How clear was the communication?
    collaboration: int      # How well did they work with others?

    # Optional feedback
    comment: Optional[str] = None
    would_use_again: bool = True

    # Metadata
    conversation_topic: Optional[str] = None
    conversation_turns: int = 0

    def __post_init__(self):
        """Validate ratings are in 1-5 range."""
        for rating_name in ['helpfulness', 'accuracy', 'relevance', 'clarity', 'collaboration']:
            value = getattr(self, rating_name)
            if not (1 <= value <= 5):
                raise ValueError(f"{rating_name} must be between 1 and 5, got {value}")

    def overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate weighted average score.

        Default weights:
        - helpfulness: 30%
        - accuracy: 25%
        - relevance: 20%
        - clarity: 15%
        - collaboration: 10%
        """
        if weights is None:
            weights = {
                'helpfulness': 0.30,
                'accuracy': 0.25,
                'relevance': 0.20,
                'clarity': 0.15,
                'collaboration': 0.10
            }

        score = (
            self.helpfulness * weights['helpfulness'] +
            self.accuracy * weights['accuracy'] +
            self.relevance * weights['relevance'] +
            self.clarity * weights['clarity'] +
            self.collaboration * weights['collaboration']
        )

        return round(score, 2)

    def quality_points(self) -> int:
        """
        Convert overall score to promotion points (0-5).

        Mapping:
        - 5.0: 5 points (perfect)
        - 4.5-4.9: 4 points (excellent)
        - 4.0-4.4: 3 points (good)
        - 3.0-3.9: 2 points (acceptable)
        - 2.0-2.9: 1 point (poor)
        - 1.0-1.9: 0 points (very poor)
        """
        score = self.overall_score()

        if score >= 5.0:
            return 5
        elif score >= 4.5:
            return 4
        elif score >= 4.0:
            return 3
        elif score >= 3.0:
            return 2
        elif score >= 2.0:
            return 1
        else:
            return 0

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
            'comment': self.comment,
            'would_use_again': self.would_use_again,
            'conversation_topic': self.conversation_topic,
            'conversation_turns': self.conversation_turns,
            'overall_score': self.overall_score(),
            'quality_points': self.quality_points()
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
            comment=data.get('comment'),
            would_use_again=data.get('would_use_again', True),
            conversation_topic=data.get('conversation_topic'),
            conversation_turns=data.get('conversation_turns', 0)
        )


@dataclass
class AgentPerformanceProfile:
    """Complete performance history for an agent."""

    agent_id: str
    agent_name: str

    # Current status
    current_rank: AgentRank = AgentRank.NOVICE
    promotion_points: int = 0

    # Usage statistics
    total_conversations: int = 0
    total_turns: int = 0
    last_used: datetime = field(default_factory=datetime.now)

    # Performance metrics
    ratings: List[ConversationRating] = field(default_factory=list)
    avg_rating: float = 0.0
    best_rating: float = 0.0
    worst_rating: float = 5.0

    # Cost tracking
    total_cost_usd: float = 0.0

    # Promotion history
    last_promoted: Optional[datetime] = None
    promotion_history: List[Dict] = field(default_factory=list)

    # Recognition
    hall_of_fame: bool = False  # God tier only
    user_favorites_count: int = 0

    def add_rating(self, rating: ConversationRating) -> Optional[AgentRank]:
        """
        Add rating, recalculate metrics, check for promotion.

        Returns:
            New rank if promoted, None otherwise
        """
        # Add rating
        self.ratings.append(rating)
        self.total_conversations += 1

        # Update points
        points_earned = rating.quality_points()
        self.promotion_points += points_earned

        # Recalculate metrics
        self._recalculate_metrics()

        # Check for promotion
        old_rank = self.current_rank
        new_rank = self._check_promotion()

        if new_rank != old_rank:
            return new_rank
        return None

    def _recalculate_metrics(self):
        """Recalculate all performance metrics."""
        if not self.ratings:
            return

        # Calculate average rating
        scores = [r.overall_score() for r in self.ratings]
        self.avg_rating = round(sum(scores) / len(scores), 2)

        # Best and worst
        self.best_rating = round(max(scores), 2)
        self.worst_rating = round(min(scores), 2)

    def _check_promotion(self) -> AgentRank:
        """Check if agent should be promoted and update rank."""
        new_rank = AgentRank.from_points(self.promotion_points)

        if new_rank != self.current_rank:
            # Record promotion
            self.promotion_history.append({
                'from_rank': self.current_rank.value,
                'to_rank': new_rank.value,
                'timestamp': datetime.now().isoformat(),
                'points': self.promotion_points
            })
            self.last_promoted = datetime.now()
            self.current_rank = new_rank

            # Check for God tier (hall of fame)
            if new_rank == AgentRank.GOD_TIER:
                self.hall_of_fame = True

        return self.current_rank

    def should_retire(self, days_unused: int) -> bool:
        """
        Determine if agent should be retired based on inactivity.

        Args:
            days_unused: Number of days since last use

        Returns:
            True if agent should be retired
        """
        # God tier never retires
        if self.current_rank == AgentRank.GOD_TIER:
            return False

        # Check against rank's protection period
        protection_days = self.current_rank.retirement_protection_days
        return days_unused > protection_days

    def cost_per_value(self) -> float:
        """
        Calculate cost efficiency (cost per promotion point).

        Lower is better. Returns 0 if no points earned.
        """
        if self.promotion_points == 0:
            return 0.0
        return round(self.total_cost_usd / self.promotion_points, 4)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'current_rank': self.current_rank.value,
            'promotion_points': self.promotion_points,
            'total_conversations': self.total_conversations,
            'total_turns': self.total_turns,
            'last_used': self.last_used.isoformat(),
            'ratings': [r.to_dict() for r in self.ratings],
            'avg_rating': self.avg_rating,
            'best_rating': self.best_rating,
            'worst_rating': self.worst_rating,
            'total_cost_usd': self.total_cost_usd,
            'last_promoted': self.last_promoted.isoformat() if self.last_promoted else None,
            'promotion_history': self.promotion_history,
            'hall_of_fame': self.hall_of_fame,
            'user_favorites_count': self.user_favorites_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentPerformanceProfile':
        """Create from dict."""
        profile = cls(
            agent_id=data['agent_id'],
            agent_name=data['agent_name'],
            current_rank=AgentRank(data['current_rank']),
            promotion_points=data['promotion_points'],
            total_conversations=data['total_conversations'],
            total_turns=data['total_turns'],
            last_used=datetime.fromisoformat(data['last_used']),
            avg_rating=data['avg_rating'],
            best_rating=data['best_rating'],
            worst_rating=data['worst_rating'],
            total_cost_usd=data['total_cost_usd'],
            last_promoted=datetime.fromisoformat(data['last_promoted']) if data.get('last_promoted') else None,
            promotion_history=data['promotion_history'],
            hall_of_fame=data['hall_of_fame'],
            user_favorites_count=data['user_favorites_count']
        )

        # Restore ratings
        profile.ratings = [ConversationRating.from_dict(r) for r in data['ratings']]

        return profile


class RatingSystem:
    """Manages agent ratings, promotions, and leaderboards."""

    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize rating system with configuration."""
        self.config = self._load_config(config_path)
        self.performance_profiles: Dict[str, AgentPerformanceProfile] = {}

    def _load_config(self, config_path: str) -> dict:
        """Load rating configuration from YAML."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('rating', {})
        except Exception as e:
            print(f"⚠️  Failed to load config: {e}, using defaults")
            return {
                'enable_post_conversation_prompt': True,
                'skip_if_short_conversation': True,
                'min_turns_for_rating': 3,
                'weights': {
                    'helpfulness': 0.30,
                    'accuracy': 0.25,
                    'relevance': 0.20,
                    'clarity': 0.15,
                    'collaboration': 0.10
                }
            }

    def submit_rating(
        self,
        agent_id: str,
        agent_name: str,
        conversation_id: str,
        helpfulness: int,
        accuracy: int,
        relevance: int,
        clarity: int,
        collaboration: int,
        comment: Optional[str] = None,
        would_use_again: bool = True,
        conversation_topic: Optional[str] = None,
        conversation_turns: int = 0
    ) -> Tuple[ConversationRating, Optional[AgentRank]]:
        """
        Submit a rating for an agent.

        Returns:
            (rating, new_rank) - new_rank is None if no promotion occurred
        """
        # Create rating
        rating = ConversationRating(
            agent_id=agent_id,
            conversation_id=conversation_id,
            timestamp=datetime.now(),
            helpfulness=helpfulness,
            accuracy=accuracy,
            relevance=relevance,
            clarity=clarity,
            collaboration=collaboration,
            comment=comment,
            would_use_again=would_use_again,
            conversation_topic=conversation_topic,
            conversation_turns=conversation_turns
        )

        # Get or create performance profile
        if agent_id not in self.performance_profiles:
            self.performance_profiles[agent_id] = AgentPerformanceProfile(
                agent_id=agent_id,
                agent_name=agent_name
            )

        profile = self.performance_profiles[agent_id]

        # Add rating and check for promotion
        new_rank = profile.add_rating(rating)

        return rating, new_rank

    def get_performance_profile(self, agent_id: str) -> Optional[AgentPerformanceProfile]:
        """Get performance profile for an agent."""
        return self.performance_profiles.get(agent_id)

    def register_agent(self, agent_id: str, agent_name: str) -> AgentPerformanceProfile:
        """Register a new agent in the rating system."""
        if agent_id not in self.performance_profiles:
            self.performance_profiles[agent_id] = AgentPerformanceProfile(
                agent_id=agent_id,
                agent_name=agent_name
            )
        return self.performance_profiles[agent_id]

    def get_leaderboard(self, top_n: int = 10) -> List[AgentPerformanceProfile]:
        """
        Get top N agents by promotion points.

        Returns:
            List of performance profiles, sorted by points (descending)
        """
        profiles = list(self.performance_profiles.values())

        # Sort by promotion points (descending), then by avg rating
        profiles.sort(
            key=lambda p: (p.promotion_points, p.avg_rating),
            reverse=True
        )

        return profiles[:top_n]

    def get_god_tier_agents(self) -> List[AgentPerformanceProfile]:
        """Get all God tier agents (hall of fame)."""
        return [
            p for p in self.performance_profiles.values()
            if p.current_rank == AgentRank.GOD_TIER
        ]

    def get_retirement_candidates(self, days_threshold: int = 90) -> List[AgentPerformanceProfile]:
        """
        Get agents eligible for retirement.

        Args:
            days_threshold: Minimum days of inactivity to consider

        Returns:
            List of agents that could be retired
        """
        now = datetime.now()
        candidates = []

        for profile in self.performance_profiles.values():
            days_unused = (now - profile.last_used).days

            if profile.should_retire(days_unused) and days_unused >= days_threshold:
                candidates.append(profile)

        # Sort by worst performers first (lowest points)
        candidates.sort(key=lambda p: p.promotion_points)

        return candidates

    def get_statistics(self) -> dict:
        """Get overall rating system statistics."""
        if not self.performance_profiles:
            return {
                'total_agents': 0,
                'total_ratings': 0,
                'avg_rating': 0.0,
                'rank_distribution': {}
            }

        profiles = list(self.performance_profiles.values())
        all_ratings = [r for p in profiles for r in p.ratings]

        # Rank distribution
        rank_dist = {}
        for rank in AgentRank:
            count = sum(1 for p in profiles if p.current_rank == rank)
            rank_dist[rank.display_name] = count

        return {
            'total_agents': len(profiles),
            'total_ratings': len(all_ratings),
            'avg_rating': round(sum(p.avg_rating for p in profiles) / len(profiles), 2) if profiles else 0.0,
            'rank_distribution': rank_dist,
            'god_tier_count': len(self.get_god_tier_agents())
        }
