"""
JSON-based persistence for Phase 1.
Phase 2 will migrate to PostgreSQL.

This module provides simple file-based storage for:
- Agent profiles (data/agents/)
- Conversation ratings (data/ratings/)
- Metadata (data/conversations/)
"""

import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from src.data_models import AgentProfile, ConversationRating


class DataStore:
    """Simple JSON-based storage for agents, ratings, and performance profiles."""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.agents_dir = self.data_dir / 'agents'
        self.ratings_dir = self.data_dir / 'ratings'
        self.conversations_dir = self.data_dir / 'conversations'
        self.performance_dir = self.data_dir / 'performance'  # NEW: Performance profiles
        self.leaderboard_dir = self.data_dir / 'leaderboard'  # NEW: Leaderboard cache

        # Create directories
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.performance_dir.mkdir(parents=True, exist_ok=True)  # NEW
        self.leaderboard_dir.mkdir(parents=True, exist_ok=True)  # NEW

    def save_agent(self, agent: AgentProfile) -> None:
        """Save agent profile to JSON file."""
        file_path = self.agents_dir / f"{agent.agent_id}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(agent.to_dict(), f, indent=2, ensure_ascii=False)

    def load_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Load agent profile from JSON file."""
        file_path = self.agents_dir / f"{agent_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return AgentProfile.from_dict(data)

    def load_all_agents(self) -> Dict[str, AgentProfile]:
        """Load all agents on startup."""
        agents = {}

        for file_path in self.agents_dir.glob("*.json"):
            agent_id = file_path.stem
            agent = self.load_agent(agent_id)
            if agent:
                agents[agent_id] = agent

        return agents

    def save_rating(self, rating: ConversationRating) -> None:
        """Save rating to JSON file."""
        # Save in agent-specific file
        agent_ratings_file = self.ratings_dir / f"{rating.agent_id}.json"

        # Load existing ratings
        if agent_ratings_file.exists():
            with open(agent_ratings_file, 'r') as f:
                ratings_data = json.load(f)
        else:
            ratings_data = []

        # Append new rating
        ratings_data.append(rating.to_dict())

        # Save back
        with open(agent_ratings_file, 'w', encoding='utf-8') as f:
            json.dump(ratings_data, f, indent=2)

    def load_agent_ratings(self, agent_id: str) -> List[ConversationRating]:
        """Load all ratings for an agent."""
        agent_ratings_file = self.ratings_dir / f"{agent_id}.json"

        if not agent_ratings_file.exists():
            return []

        with open(agent_ratings_file, 'r') as f:
            ratings_data = json.load(f)

        return [ConversationRating.from_dict(r) for r in ratings_data]

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent (retirement)."""
        file_path = self.agents_dir / f"{agent_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def get_agent_count(self) -> int:
        """Get total number of stored agents."""
        return len(list(self.agents_dir.glob("*.json")))

    def get_all_agent_ids(self) -> List[str]:
        """Get list of all agent IDs."""
        return [f.stem for f in self.agents_dir.glob("*.json")]

    # ========== Performance Profile Methods (Phase 1D) ==========

    def save_performance_profile(self, profile) -> None:
        """
        Save agent performance profile to JSON file.

        Args:
            profile: AgentPerformanceProfile instance
        """
        file_path = self.performance_dir / f"{profile.agent_id}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

    def load_performance_profile(self, agent_id: str):
        """
        Load agent performance profile from JSON file.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentPerformanceProfile instance or None
        """
        file_path = self.performance_dir / f"{agent_id}.json"

        if not file_path.exists():
            return None

        # Import here to avoid circular dependency
        from src.rating_system import AgentPerformanceProfile

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return AgentPerformanceProfile.from_dict(data)

    def load_all_performance_profiles(self) -> Dict:
        """
        Load all performance profiles on startup.

        Returns:
            Dict of agent_id -> AgentPerformanceProfile
        """
        profiles = {}

        for file_path in self.performance_dir.glob("*.json"):
            agent_id = file_path.stem
            profile = self.load_performance_profile(agent_id)
            if profile:
                profiles[agent_id] = profile

        return profiles

    def delete_performance_profile(self, agent_id: str) -> bool:
        """
        Delete performance profile (when agent retired).

        Args:
            agent_id: Agent identifier

        Returns:
            True if deleted, False if not found
        """
        file_path = self.performance_dir / f"{agent_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    # ========== Leaderboard Caching Methods (Phase 1D) ==========

    def save_leaderboard(self, leaderboard_data: dict) -> None:
        """
        Save leaderboard snapshot to cache.

        Args:
            leaderboard_data: Dict with leaderboard info
        """
        file_path = self.leaderboard_dir / "current.json"

        # Add timestamp
        leaderboard_data['generated_at'] = datetime.now().isoformat()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(leaderboard_data, f, indent=2)

    def load_leaderboard(self) -> Optional[dict]:
        """
        Load cached leaderboard.

        Returns:
            Leaderboard dict or None if not cached
        """
        file_path = self.leaderboard_dir / "current.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_leaderboard_stale(self, max_age_seconds: int = 300) -> bool:
        """
        Check if cached leaderboard is stale.

        Args:
            max_age_seconds: Maximum age in seconds (default: 5 minutes)

        Returns:
            True if stale or doesn't exist
        """
        leaderboard = self.load_leaderboard()

        if not leaderboard or 'generated_at' not in leaderboard:
            return True

        generated_at = datetime.fromisoformat(leaderboard['generated_at'])
        age_seconds = (datetime.now() - generated_at).total_seconds()

        return age_seconds > max_age_seconds
