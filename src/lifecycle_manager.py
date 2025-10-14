"""
Lifecycle Manager - Agent tier management and retirement decisions

This module manages agent lifecycle tiers based on usage patterns:
- HOT: Currently active in conversation
- WARM: Used within 7 days (instant retrieval, memory resident)
- COLD: Used 7-90 days ago (disk storage, slower retrieval)
- ARCHIVED: 90+ days unused (retirement candidate)
- RETIRED: Deleted (only metadata preserved)

Retirement decisions respect agent ranks:
- NOVICE: 7 days protection
- COMPETENT: 30 days protection
- EXPERT: 90 days protection
- MASTER: 180 days protection
- LEGENDARY: 365 days protection
- GOD_TIER: Never retired
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import yaml

from src.rating_system import AgentRank, AgentPerformanceProfile


class AgentTier(Enum):
    """Agent lifecycle tiers based on usage recency."""

    HOT = "hot"          # Currently active in conversation
    WARM = "warm"        # Used within 7 days (instant retrieval)
    COLD = "cold"        # Used 7-90 days ago (disk storage)
    ARCHIVED = "archived" # 90+ days, candidate for retirement
    RETIRED = "retired"   # Deleted, pattern saved

    @property
    def icon(self) -> str:
        """Visual icon for tier."""
        icons = {
            AgentTier.HOT: "🔥",
            AgentTier.WARM: "☀️",
            AgentTier.COLD: "❄️",
            AgentTier.ARCHIVED: "📦",
            AgentTier.RETIRED: "💤"
        }
        return icons[self]

    @property
    def display_name(self) -> str:
        """Human-readable tier name."""
        return self.value.title()

    @property
    def description(self) -> str:
        """Description of tier."""
        descriptions = {
            AgentTier.HOT: "Active in current conversation",
            AgentTier.WARM: "Used recently (within 7 days)",
            AgentTier.COLD: "Not used recently (7-90 days)",
            AgentTier.ARCHIVED: "Inactive for 90+ days",
            AgentTier.RETIRED: "Removed from active service"
        }
        return descriptions[self]


@dataclass
class TierTransition:
    """Record of an agent moving between tiers."""

    agent_id: str
    from_tier: AgentTier
    to_tier: AgentTier
    timestamp: datetime
    reason: str

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'agent_id': self.agent_id,
            'from_tier': self.from_tier.value,
            'to_tier': self.to_tier.value,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason
        }


class LifecycleManager:
    """Manages agent lifecycle tiers and retirement decisions."""

    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize lifecycle manager with configuration."""
        self.config = self._load_config(config_path)

        # Tier thresholds (days)
        self.warm_days = self.config.get('warm_days', 7)
        self.cold_days = self.config.get('cold_days', 90)
        self.archive_days = self.config.get('archive_days', 180)
        self.enable_auto_retirement = self.config.get('enable_auto_retirement', False)

        # Track active tiers
        self.agent_tiers: Dict[str, AgentTier] = {}
        self.hot_agents: Set[str] = set()  # Currently in conversation
        self.transition_history: List[TierTransition] = []

    def _load_config(self, config_path: str) -> dict:
        """Load lifecycle configuration from YAML."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('agent_lifecycle', {})
        except Exception as e:
            print(f"⚠️  Failed to load config: {e}, using defaults")
            return {
                'warm_days': 7,
                'cold_days': 90,
                'archive_days': 180,
                'enable_auto_retirement': False
            }

    def determine_tier(
        self,
        agent_id: str,
        last_used: datetime,
        current_rank: AgentRank = AgentRank.NOVICE
    ) -> AgentTier:
        """
        Determine appropriate tier for an agent based on last use.

        Args:
            agent_id: Agent identifier
            last_used: When agent was last used
            current_rank: Agent's current rank (for context)

        Returns:
            Appropriate tier
        """
        # Check if currently hot
        if agent_id in self.hot_agents:
            return AgentTier.HOT

        # Calculate days since last use
        now = datetime.now()
        days_unused = (now - last_used).days

        # Determine tier based on days
        if days_unused <= self.warm_days:
            return AgentTier.WARM
        elif days_unused <= self.cold_days:
            return AgentTier.COLD
        else:
            # Check if should be retired
            if self._should_retire(agent_id, days_unused, current_rank):
                return AgentTier.RETIRED
            else:
                return AgentTier.ARCHIVED

    def mark_hot(self, agent_id: str):
        """Mark agent as HOT (currently in use)."""
        old_tier = self.agent_tiers.get(agent_id, AgentTier.WARM)
        self.hot_agents.add(agent_id)
        self.agent_tiers[agent_id] = AgentTier.HOT

        if old_tier != AgentTier.HOT:
            self._record_transition(
                agent_id,
                old_tier,
                AgentTier.HOT,
                "Agent selected for conversation"
            )

    def mark_inactive(self, agent_id: str):
        """Remove HOT status when conversation ends."""
        if agent_id in self.hot_agents:
            self.hot_agents.remove(agent_id)

            # Agent returns to WARM tier after use
            old_tier = self.agent_tiers.get(agent_id, AgentTier.HOT)
            self.agent_tiers[agent_id] = AgentTier.WARM

            if old_tier != AgentTier.WARM:
                self._record_transition(
                    agent_id,
                    old_tier,
                    AgentTier.WARM,
                    "Conversation ended, agent becomes warm"
                )

    def update_tier(
        self,
        agent_id: str,
        last_used: datetime,
        current_rank: AgentRank = AgentRank.NOVICE
    ) -> AgentTier:
        """
        Update agent's tier based on current state.

        Args:
            agent_id: Agent identifier
            last_used: When agent was last used
            current_rank: Agent's current rank

        Returns:
            New tier (may be same as before)
        """
        old_tier = self.agent_tiers.get(agent_id, AgentTier.WARM)
        new_tier = self.determine_tier(agent_id, last_used, current_rank)

        if new_tier != old_tier:
            self.agent_tiers[agent_id] = new_tier
            self._record_transition(
                agent_id,
                old_tier,
                new_tier,
                f"Tier updated based on {(datetime.now() - last_used).days} days of inactivity"
            )

        return new_tier

    def get_tier(self, agent_id: str) -> AgentTier:
        """Get current tier for an agent."""
        return self.agent_tiers.get(agent_id, AgentTier.WARM)

    def _should_retire(
        self,
        agent_id: str,
        days_unused: int,
        current_rank: AgentRank
    ) -> bool:
        """
        Determine if agent should be retired.

        Respects rank-based protection periods.
        """
        # Check if auto-retirement is enabled
        if not self.enable_auto_retirement:
            return False

        # God tier never retires
        if current_rank == AgentRank.GOD_TIER:
            return False

        # Check against rank's protection period
        protection_days = current_rank.retirement_protection_days
        return days_unused > protection_days

    def check_retirement_eligibility(
        self,
        agent_id: str,
        last_used: datetime,
        current_rank: AgentRank,
        performance_profile: Optional[AgentPerformanceProfile] = None
    ) -> Dict:
        """
        Comprehensive retirement eligibility check.

        Args:
            agent_id: Agent identifier
            last_used: When agent was last used
            current_rank: Agent's current rank
            performance_profile: Optional performance data

        Returns:
            Dict with:
            - eligible: bool
            - reason: str
            - days_unused: int
            - protection_remaining: int (days)
        """
        now = datetime.now()
        days_unused = (now - last_used).days
        protection_days = current_rank.retirement_protection_days

        # God tier special case
        if current_rank == AgentRank.GOD_TIER:
            return {
                'eligible': False,
                'reason': '🌟 God tier agents never retire',
                'days_unused': days_unused,
                'protection_remaining': 99999
            }

        # Check if past protection period
        if days_unused <= protection_days:
            return {
                'eligible': False,
                'reason': f'{current_rank.icon} Still protected by {current_rank.display_name} rank',
                'days_unused': days_unused,
                'protection_remaining': protection_days - days_unused
            }

        # Eligible for retirement
        reason = f'Unused for {days_unused} days (>{protection_days} day protection)'

        # Add performance context if available
        if performance_profile:
            if performance_profile.avg_rating < 3.0:
                reason += f', low rating ({performance_profile.avg_rating}/5.0)'
            elif performance_profile.total_conversations == 0:
                reason += ', never used in conversation'

        return {
            'eligible': True,
            'reason': reason,
            'days_unused': days_unused,
            'protection_remaining': 0
        }

    def retire_agent(self, agent_id: str, reason: str = "Automatic retirement"):
        """
        Mark agent as retired.

        Args:
            agent_id: Agent to retire
            reason: Reason for retirement
        """
        old_tier = self.agent_tiers.get(agent_id, AgentTier.ARCHIVED)
        self.agent_tiers[agent_id] = AgentTier.RETIRED

        # Remove from hot agents if present
        self.hot_agents.discard(agent_id)

        self._record_transition(
            agent_id,
            old_tier,
            AgentTier.RETIRED,
            reason
        )

    def cleanup_pass(
        self,
        agents_with_profiles: Dict[str, tuple]  # (last_used, rank, profile)
    ) -> List[str]:
        """
        Perform periodic cleanup to update tiers and identify retirement candidates.

        Args:
            agents_with_profiles: Dict of agent_id -> (last_used, rank, profile)

        Returns:
            List of agent IDs eligible for retirement
        """
        retirement_candidates = []

        for agent_id, (last_used, rank, profile) in agents_with_profiles.items():
            # Skip hot agents
            if agent_id in self.hot_agents:
                continue

            # Update tier
            new_tier = self.update_tier(agent_id, last_used, rank)

            # Check retirement eligibility
            if new_tier == AgentTier.ARCHIVED:
                eligibility = self.check_retirement_eligibility(
                    agent_id,
                    last_used,
                    rank,
                    profile
                )

                if eligibility['eligible']:
                    retirement_candidates.append(agent_id)

        return retirement_candidates

    def get_tier_distribution(self) -> Dict[AgentTier, int]:
        """Get count of agents in each tier."""
        distribution = {tier: 0 for tier in AgentTier}

        for tier in self.agent_tiers.values():
            distribution[tier] += 1

        return distribution

    def get_agents_by_tier(self, tier: AgentTier) -> List[str]:
        """Get all agent IDs in a specific tier."""
        return [
            agent_id for agent_id, agent_tier in self.agent_tiers.items()
            if agent_tier == tier
        ]

    def _record_transition(
        self,
        agent_id: str,
        from_tier: AgentTier,
        to_tier: AgentTier,
        reason: str
    ):
        """Record a tier transition for history."""
        transition = TierTransition(
            agent_id=agent_id,
            from_tier=from_tier,
            to_tier=to_tier,
            timestamp=datetime.now(),
            reason=reason
        )
        self.transition_history.append(transition)

    def get_transition_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[TierTransition]:
        """
        Get tier transition history.

        Args:
            agent_id: Optional agent ID to filter by
            limit: Maximum number of transitions to return

        Returns:
            List of transitions (most recent first)
        """
        history = self.transition_history

        if agent_id:
            history = [t for t in history if t.agent_id == agent_id]

        # Sort by timestamp (most recent first)
        history.sort(key=lambda t: t.timestamp, reverse=True)

        return history[:limit]

    def get_statistics(self) -> dict:
        """Get lifecycle manager statistics."""
        distribution = self.get_tier_distribution()

        return {
            'total_agents': len(self.agent_tiers),
            'hot_agents': len(self.hot_agents),
            'tier_distribution': {
                tier.display_name: count
                for tier, count in distribution.items()
            },
            'total_transitions': len(self.transition_history),
            'auto_retirement_enabled': self.enable_auto_retirement,
            'thresholds': {
                'warm_days': self.warm_days,
                'cold_days': self.cold_days,
                'archive_days': self.archive_days
            }
        }
