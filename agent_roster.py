"""
Agent Roster Management - View and manage dynamic agents

This module provides a comprehensive interface for viewing and managing
the dynamic agent roster. Features include:
- Paginated agent list with filtering and sorting
- Detailed agent profiles with performance history
- System-wide statistics dashboard

Usage:
    from agent_roster import AgentRoster
    from src.persistence import DataStore

    roster = AgentRoster(DataStore())
    roster.show_agent_list()
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from src.persistence import DataStore
from src.data_models import AgentProfile, AgentDomain
from src.rating_system import AgentPerformanceProfile, AgentRank


class AgentRoster:
    """Manages agent roster viewing and inspection."""

    def __init__(self, data_store: DataStore):
        """
        Initialize agent roster manager.

        Args:
            data_store: DataStore instance for accessing agent data
        """
        self.data_store = data_store
        self.agents_dir = Path('.claude/agents/dynamic')

        # Cache for performance (loaded once per session)
        self._agents_cache: Optional[Dict[str, AgentProfile]] = None
        self._profiles_cache: Optional[Dict[str, AgentPerformanceProfile]] = None
        self._cached_agent_list: Optional[List[Tuple[str, AgentProfile]]] = None

    def _load_agents(self) -> Dict[str, AgentProfile]:
        """Load all agents (with caching)."""
        if self._agents_cache is None:
            self._agents_cache = self.data_store.load_all_agents()
        return self._agents_cache

    def _load_profiles(self) -> Dict[str, AgentPerformanceProfile]:
        """Load all performance profiles (with caching)."""
        if self._profiles_cache is None:
            self._profiles_cache = self.data_store.load_all_performance_profiles()
        return self._profiles_cache

    def _get_agent_tier(self, agent: AgentProfile) -> str:
        """
        Calculate agent tier based on last usage.

        Returns:
            Tier icon and name (HOT/WARM/COLD)
        """
        days_since = (datetime.now() - agent.last_used).days

        if days_since == 0:
            return "🟢 HOT"
        elif days_since <= 7:
            return "🟡 WARM"
        else:
            return "🔵 COLD"

    def show_agent_list(
        self,
        filter_domain: Optional[str] = None,
        sort_by: str = 'rating',
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Tuple[str, AgentProfile]], int]:
        """
        Display paginated agent list with filtering and sorting.

        Args:
            filter_domain: Domain to filter by (None = all)
            sort_by: Sort criterion ('rating', 'uses', 'last_used', 'name', 'rank')
            search: Search query for name/keywords
            page: Current page number (1-indexed)
            page_size: Number of agents per page

        Returns:
            Tuple of (page_agents, total_pages)
        """
        # Load data
        all_agents = self._load_agents()
        all_profiles = self._load_profiles()

        # Apply filters
        agents = self._filter_agents(all_agents, all_profiles, filter_domain, search)

        # Sort
        agents = self._sort_agents(agents, all_profiles, sort_by)

        # Paginate
        total_pages = max(1, (len(agents) + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))  # Clamp to valid range
        start = (page - 1) * page_size
        end = start + page_size
        page_agents = agents[start:end]

        # Display
        self._render_agent_list(
            page_agents,
            all_profiles,
            page,
            total_pages,
            len(agents),
            filter_domain,
            sort_by
        )

        return page_agents, total_pages

    def show_agent_details(self, agent_id: str) -> bool:
        """
        Display detailed view of a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent found and displayed, False otherwise
        """
        agent = self.data_store.load_agent(agent_id)
        if not agent:
            print(f"\n❌ Agent not found: {agent_id}")
            return False

        profile = self.data_store.load_performance_profile(agent_id)

        self._render_agent_details(agent, profile)
        return True

    def show_statistics_dashboard(self):
        """Display overall agent system statistics."""
        all_agents = self._load_agents()
        all_profiles = self._load_profiles()

        stats = self._calculate_statistics(all_agents, all_profiles)
        self._render_statistics(stats)

    # ========== Private Helper Methods ==========

    def _filter_agents(
        self,
        agents: Dict[str, AgentProfile],
        profiles: Dict[str, AgentPerformanceProfile],
        domain: Optional[str],
        search: Optional[str]
    ) -> List[Tuple[str, AgentProfile]]:
        """Apply domain and search filters."""
        filtered = []

        for agent_id, agent in agents.items():
            # Domain filter
            if domain and domain != "All Domains":
                if agent.domain.value != domain.lower():
                    continue

            # Search filter
            if search:
                search_lower = search.lower()
                # Search in name, keywords, specialization, unique expertise
                if not (
                    search_lower in agent.name.lower() or
                    any(search_lower in kw.lower() for kw in agent.keywords) or
                    search_lower in agent.specialization.lower() or
                    search_lower in agent.unique_expertise.lower()
                ):
                    continue

            filtered.append((agent_id, agent))

        return filtered

    def _sort_agents(
        self,
        agents: List[Tuple[str, AgentProfile]],
        profiles: Dict[str, AgentPerformanceProfile],
        sort_by: str
    ) -> List[Tuple[str, AgentProfile]]:
        """Sort agents by specified criterion."""

        if sort_by == 'rating':
            # Sort by average rating (descending)
            return sorted(
                agents,
                key=lambda x: profiles.get(x[0], None).avg_rating if profiles.get(x[0]) else 0,
                reverse=True
            )
        elif sort_by == 'uses':
            # Sort by total uses (descending)
            return sorted(
                agents,
                key=lambda x: profiles.get(x[0], None).total_conversations if profiles.get(x[0]) else 0,
                reverse=True
            )
        elif sort_by == 'last_used':
            # Sort by last used (most recent first)
            return sorted(
                agents,
                key=lambda x: x[1].last_used,
                reverse=True
            )
        elif sort_by == 'name':
            # Sort alphabetically by name
            return sorted(agents, key=lambda x: x[1].name.lower())
        elif sort_by == 'rank':
            # Sort by rank (highest first)
            return sorted(
                agents,
                key=lambda x: profiles.get(x[0], None).current_rank.value if profiles.get(x[0]) else 0,
                reverse=True
            )
        else:
            # Default: rating
            return sorted(
                agents,
                key=lambda x: profiles.get(x[0], None).avg_rating if profiles.get(x[0]) else 0,
                reverse=True
            )

    def _render_agent_list(
        self,
        agents: List[Tuple[str, AgentProfile]],
        profiles: Dict[str, AgentPerformanceProfile],
        page: int,
        total_pages: int,
        total_agents: int,
        filter_domain: Optional[str],
        sort_by: str
    ):
        """Render the agent list view."""
        print("\n" + "=" * 100)
        print(f"👥 AGENT ROSTER ({total_agents} Agent{'s' if total_agents != 1 else ''})")
        print("=" * 100)

        # Show filter/sort status
        filter_str = filter_domain if filter_domain else "All Domains"
        sort_str = {
            'rating': 'Rating',
            'uses': 'Uses',
            'last_used': 'Last Used',
            'name': 'Name',
            'rank': 'Rank'
        }.get(sort_by, 'Rating')
        print(f"\nFilter: {filter_str} | Sort: {sort_str} | Page: {page}/{total_pages}")

        if not agents:
            print("\n❌ No agents found matching your criteria.")
            print("\n[b] Back")
            return

        # Header
        print("\n" + "-" * 100)
        print(f"{'#':<4} {'Name':<30} {'Domain':<13} {'Rank':<14} {'Rating':<9} {'Uses':<6} {'Last Used':<12}")
        print("-" * 100)

        # Agent rows
        start_num = (page - 1) * 20 + 1
        for idx, (agent_id, agent) in enumerate(agents, start=start_num):
            profile = profiles.get(agent_id)

            # Name (truncate if too long)
            name = agent.name[:28] + ".." if len(agent.name) > 28 else agent.name

            # Domain icon + name
            domain_str = f"{agent.domain.icon} {agent.domain.value.title()}"

            # Rank with icon
            if profile:
                rank_str = f"{profile.current_rank.icon} {profile.current_rank.display_name}"
                rating_str = f"{profile.avg_rating:.1f}/5.0"
                uses_str = str(profile.total_conversations)
            else:
                rank_str = "📗 NOVICE"
                rating_str = "N/A"
                uses_str = "0"

            # Last used date
            last_used = agent.last_used.strftime("%Y-%m-%d") if agent.last_used else "Never"

            print(f"{idx:<4} {name:<30} {domain_str:<20} {rank_str:<21} {rating_str:<9} {uses_str:<6} {last_used:<12}")

        # Footer with commands
        print("-" * 100)
        print("\nCommands:")
        print("  [#] View agent details | [f] Filter by domain | [s] Search | [o] Sort options")
        if total_pages > 1:
            print(f"  [n] Next page | [p] Previous page", end="")
        print(" | [b] Back to Settings")

    def _render_agent_details(
        self,
        agent: AgentProfile,
        profile: Optional[AgentPerformanceProfile]
    ):
        """Render detailed agent view."""
        print("\n" + "=" * 100)
        print("👤 AGENT PROFILE")
        print("=" * 100)

        # Basic info
        print(f"\nName:           {agent.name}")
        print(f"Agent ID:       {agent.agent_id}")
        print(f"Domain:         {agent.domain.icon}  {agent.domain.value.title()}")
        print(f"Classification: {agent.primary_class}")
        print(f"Specialization: {agent.specialization}")

        # Rank and status
        if profile:
            rank_str = f"{profile.current_rank.icon} {profile.current_rank.display_name} ({profile.promotion_points} points)"
            status_str = self._get_agent_tier(agent)
            print(f"Rank:           {rank_str}")
            print(f"Status:         {status_str}")
        else:
            print(f"Rank:           📗 NOVICE (0 points)")
            print(f"Status:         🟢 NEW")

        # Core skills
        print(f"\nCore Skills:")
        for skill in agent.core_skills[:5]:  # Show first 5
            print(f"  • {skill}")

        # Keywords
        keywords_str = ', '.join(list(agent.keywords)[:15])  # Show first 15
        if len(agent.keywords) > 15:
            keywords_str += ", ..."
        print(f"\nKeywords:")
        print(f"  {keywords_str}")

        # Performance statistics
        if profile:
            print(f"\n📊 Performance Statistics:")
            print(f"  Total Uses:        {profile.total_conversations} conversation{'s' if profile.total_conversations != 1 else ''}")
            print(f"  Average Rating:    {profile.avg_rating:.1f}/5.0")
            print(f"  Best Rating:       {profile.best_rating:.1f}/5.0")
            print(f"  Worst Rating:      {profile.worst_rating:.1f}/5.0")
            if hasattr(agent, 'creation_cost_usd'):
                print(f"  Creation Cost:     ${agent.creation_cost_usd:.4f}")
            if profile.total_cost_usd > 0:
                print(f"  Total Cost:        ${profile.total_cost_usd:.4f}")
            print(f"  Created:           {agent.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Last Used:         {agent.last_used.strftime('%Y-%m-%d %H:%M')}")

            # Rating history (last 5)
            if profile.ratings:
                print(f"\n📈 Recent Rating History:")
                for rating in profile.ratings[-5:]:
                    stars = "⭐" * int(round(rating.overall_score()))
                    print(f"  {rating.timestamp.strftime('%Y-%m-%d')}: {stars} {rating.overall_score():.1f}/5.0 " +
                          f"(H:{rating.helpfulness}, A:{rating.accuracy}, R:{rating.relevance}, " +
                          f"C:{rating.clarity}, Col:{rating.collaboration})")
        else:
            print(f"\n📊 Performance Statistics:")
            print(f"  Total Uses:        0 conversations")
            print(f"  Average Rating:    N/A (no ratings yet)")
            print(f"  Created:           {agent.created_at.strftime('%Y-%m-%d %H:%M')}")

        # System prompt preview
        prompt_preview = agent.system_prompt[:200] if agent.system_prompt else "N/A"
        if len(agent.system_prompt) > 200:
            prompt_preview += "..."
        word_count = len(agent.system_prompt.split()) if agent.system_prompt else 0

        print(f"\n📝 System Prompt Preview:")
        print(f"  {prompt_preview}")
        print(f"  [Full prompt: {word_count} words]")

        print("\n" + "=" * 100)
        print("\nActions:")
        print("  [v] View Full System Prompt | [b] Back to Agent List")

    def _calculate_statistics(
        self,
        agents: Dict[str, AgentProfile],
        profiles: Dict[str, AgentPerformanceProfile]
    ) -> dict:
        """Calculate comprehensive system statistics."""
        now = datetime.now()

        # Basic counts
        total_agents = len(agents)
        total_conversations = sum(p.total_conversations for p in profiles.values())
        total_cost = sum(
            p.total_cost_usd for p in profiles.values()
        ) + sum(
            getattr(a, 'creation_cost_usd', 0) for a in agents.values()
        )

        # Average rating
        ratings = [p.avg_rating for p in profiles.values() if p.avg_rating > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

        # Activity metrics
        active_today = sum(1 for a in agents.values() if (now - a.last_used).days == 0)
        created_today = sum(1 for a in agents.values() if (now - a.created_at).days == 0)
        inactive_7days = sum(1 for a in agents.values() if (now - a.last_used).days > 7)
        inactive_90days = sum(1 for a in agents.values() if (now - a.last_used).days > 90)

        # Top performers by rating
        top_by_rating = sorted(
            [(p, agents.get(p.agent_id)) for p in profiles.values() if p.avg_rating > 0],
            key=lambda x: x[0].avg_rating,
            reverse=True
        )[:5]

        # Most used agents
        top_by_uses = sorted(
            [(p, agents.get(p.agent_id)) for p in profiles.values() if p.total_conversations > 0],
            key=lambda x: x[0].total_conversations,
            reverse=True
        )[:5]

        # Rank distribution
        rank_dist = {}
        for rank in AgentRank:
            count = sum(1 for p in profiles.values() if p.current_rank == rank)
            rank_dist[rank] = count

        # Domain distribution
        domain_dist = {}
        for domain in AgentDomain:
            count = sum(1 for a in agents.values() if a.domain == domain)
            if count > 0:
                domain_dist[domain] = count

        return {
            'total_agents': total_agents,
            'total_conversations': total_conversations,
            'total_cost': total_cost,
            'avg_rating': avg_rating,
            'active_today': active_today,
            'created_today': created_today,
            'inactive_7days': inactive_7days,
            'inactive_90days': inactive_90days,
            'top_by_rating': top_by_rating,
            'top_by_uses': top_by_uses,
            'rank_dist': rank_dist,
            'domain_dist': domain_dist
        }

    def _render_statistics(self, stats: dict):
        """Render statistics dashboard."""
        print("\n" + "=" * 100)
        print("📊 AGENT SYSTEM STATISTICS")
        print("=" * 100)

        # Overview
        print(f"\n📈 Overview:")
        print(f"  Total Agents:           {stats['total_agents']}")
        print(f"  Active Agents:          {stats['active_today']} (🟢 used today)")
        print(f"  Total Conversations:    {stats['total_conversations']}")
        print(f"  Average Rating:         {stats['avg_rating']:.2f}/5.0")
        print(f"  Total System Cost:      ${stats['total_cost']:.4f}")

        # Top performers by rating
        if stats['top_by_rating']:
            print(f"\n🏆 Top Performers (by rating):")
            for idx, (profile, agent) in enumerate(stats['top_by_rating'], 1):
                if agent:
                    print(f"  {idx}. {agent.name:<30} {agent.domain.icon} {agent.domain.value.title():<15} " +
                          f"{profile.avg_rating:.1f}/5 ({profile.total_conversations} uses)")

        # Most used agents
        if stats['top_by_uses']:
            print(f"\n💪 Most Used Agents:")
            for idx, (profile, agent) in enumerate(stats['top_by_uses'], 1):
                if agent:
                    print(f"  {idx}. {agent.name:<30} {agent.domain.icon} {agent.domain.value.title():<15} " +
                          f"{profile.total_conversations} uses")

        # Agents by rank
        print(f"\n📊 Agents by Rank:")
        for rank in reversed(list(AgentRank)):
            count = stats['rank_dist'].get(rank, 0)
            points = f"{rank.min_points}+"
            if rank == AgentRank.NOVICE:
                points = "0-9"
            elif rank == AgentRank.COMPETENT:
                points = "10-24"
            elif rank == AgentRank.EXPERT:
                points = "25-49"
            elif rank == AgentRank.MASTER:
                points = "50-99"
            elif rank == AgentRank.LEGENDARY:
                points = "100-199"
            elif rank == AgentRank.GOD_TIER:
                points = "200+"
            print(f"  {rank.icon} {rank.display_name:<12} ({points:<8}points): {count:>3} agent{'s' if count != 1 else ''}")

        # Agents by domain
        print(f"\n🌍 Agents by Domain:")
        for domain, count in sorted(stats['domain_dist'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain.icon} {domain.value.title():<15}: {count:>2} agent{'s' if count != 1 else ''}")

        # Activity
        print(f"\n📅 Activity:")
        print(f"  Created today:          {stats['created_today']} agents")
        print(f"  Used today:             {stats['active_today']} agents")
        print(f"  Inactive (>7 days):     {stats['inactive_7days']} agents (🟡 WARM)")
        print(f"  Inactive (>90 days):    {stats['inactive_90days']} agents (🔵 COLD)")

        print("\n" + "=" * 100)
        print("\n[Press Enter to return to Settings menu]")
