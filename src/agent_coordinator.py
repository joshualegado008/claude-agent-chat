"""
Agent Coordinator - Orchestrates all agent management systems

This is the central brain of the Phase 1 dynamic multi-agent system that:
- Coordinates agent creation and reuse
- Manages ratings and promotions
- Handles lifecycle transitions
- Persists all state
- Provides clean API for main coordinator
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid
from pathlib import Path

from src.agent_taxonomy import AgentTaxonomy
from src.agent_factory import AgentFactory
from src.deduplication import AgentDeduplicationSystem
from src.rating_system import RatingSystem, AgentRank
from src.lifecycle_manager import LifecycleManager, AgentTier
from src.persistence import DataStore
from src.data_models import AgentProfile
from metadata_extractor import MetadataExtractor
from display_formatter import DisplayFormatter


class AgentCoordinator:
    """
    Central orchestration for all agent systems.

    Responsibilities:
    1. Load existing agents on startup
    2. Coordinate agent creation/reuse
    3. Manage ratings and promotions
    4. Handle lifecycle transitions
    5. Persist all state changes
    6. Provide clean API for conversations
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize all subsystems.

        Args:
            verbose: If True, print status messages
        """
        self.verbose = verbose

        # Initialize all systems
        if self.verbose:
            print("🔧 Initializing agent management systems...")

        self.taxonomy = AgentTaxonomy()
        self.factory = AgentFactory(self.taxonomy)
        self.deduplication = AgentDeduplicationSystem(self.taxonomy)
        self.rating_system = RatingSystem()
        self.lifecycle_manager = LifecycleManager()
        self.store = DataStore()
        self.metadata_extractor = MetadataExtractor()

        # Track active agents in current session
        self.active_agents: Dict[str, AgentProfile] = {}

        # Load existing state from disk
        self._load_state()

        if self.verbose:
            print(f"✅ Loaded {len(self.active_agents)} existing agents")

    def _load_state(self):
        """
        Load all persisted state on startup.

        Steps:
        1. Load all agent profiles
        2. Load all performance profiles
        3. Register agents with deduplication system
        4. Update lifecycle tiers
        5. Rebuild leaderboard cache
        """

        # Load agent profiles from data/agents/
        agents_dir = self.store.data_dir / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.json"):
                try:
                    agent = self.store.load_agent(agent_file.stem)
                    if agent:
                        self.active_agents[agent.agent_id] = agent
                        self.deduplication.register_agent(agent)
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Error loading agent {agent_file.name}: {e}")

        # Load performance profiles from data/performance/
        perf_dir = self.store.data_dir / "performance"
        if perf_dir.exists():
            for perf_file in perf_dir.glob("*.json"):
                try:
                    profile = self.store.load_performance_profile(perf_file.stem)
                    if profile:
                        self.rating_system.performance_profiles[profile.agent_id] = profile
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Error loading performance {perf_file.name}: {e}")

        # Update lifecycle tiers for all agents
        for agent_id in self.active_agents.keys():
            try:
                self.lifecycle_manager.update_tier(agent_id, self.rating_system)
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Error updating tier for {agent_id}: {e}")

    async def get_or_create_agents(
        self,
        raw_topic: str
    ) -> Tuple[List[AgentProfile], Dict[str, any]]:
        """
        Main orchestration method for agent acquisition.

        Process:
        1. Refine topic using OpenAI 4o-mini
        2. Analyze expertise requirements
        3. For each required expertise:
           a. Check if suitable agent exists (deduplication)
           b. If exists: reuse (cache hit)
           c. If not: create new agent
        4. Update lifecycle tiers (mark as HOT/used)
        5. Return agents and metadata

        Args:
            raw_topic: User's original topic input

        Returns:
            Tuple of:
            - List[AgentProfile]: Agents to use in conversation
            - Dict: Metadata (refined_topic, creation_cost, cache_hits, etc.)
        """

        metadata = {
            'refined_topic': '',
            'expertise_requirements': [],
            'agents_created': 0,
            'agents_reused': 0,
            'creation_cost': 0.0,
            'cache_savings': 0.0
        }

        if self.verbose:
            print(f"\n🔄 Refining topic...")

        # Step 1: Refine topic
        refined_topic = await self.metadata_extractor.refine_topic(raw_topic)
        metadata['refined_topic'] = refined_topic

        if self.verbose:
            print(f"\n✨ Enhanced Topic:")
            print(f'"{refined_topic}"')

        # Step 2: Analyze expertise requirements
        if self.verbose:
            print(f"\n🧠 Analyzing expertise requirements...\n")

        expertise_analysis = await self.metadata_extractor.analyze_expertise_requirements(
            refined_topic
        )

        metadata['expertise_requirements'] = expertise_analysis.get('expertise_needed', [])

        if self.verbose:
            print("Required expertise:")
            for exp in metadata['expertise_requirements']:
                print(f"  • {exp}")

        # Step 3: Get or create agents for each expertise
        if self.verbose:
            print(f"\n{'━' * 60}")
            print("🔍 Checking for existing agents...\n")

        agents_to_use = []

        for expertise_desc in metadata['expertise_requirements']:
            # Check deduplication
            decision = self.deduplication.check_before_create(
                expertise_desc,
                strict=True
            )

            if decision['action'] == 'reuse':
                # Cache hit! Reuse existing agent
                agent_id = decision['agent_id']
                agent = self.active_agents[agent_id]

                if self.verbose:
                    print(f"✅ Reusing: {agent.name}")
                    print(f"   └─ {decision['reason']}")

                agents_to_use.append(agent)
                metadata['agents_reused'] += 1
                metadata['cache_savings'] += 0.004  # Approximate agent creation cost

            elif decision['action'] in ['create', 'create_with_warning']:
                # Need to create new agent
                if self.verbose:
                    print(f"❌ Not found: {expertise_desc[:50]}...")
                    print(f"   Creating new expert...\n")

                # Create agent
                agent = await self.factory.create_agent(
                    expertise_desc,
                    classification=decision.get('classification'),
                    context=refined_topic
                )

                # Register in all systems
                self.active_agents[agent.agent_id] = agent
                self.deduplication.register_agent(agent)

                # Initialize performance profile
                self.rating_system.register_agent(
                    agent.agent_id,
                    agent.name
                )

                # Save to disk
                self.store.save_agent(agent)

                agents_to_use.append(agent)
                metadata['agents_created'] += 1
                metadata['creation_cost'] += self.factory.get_total_cost()

            else:
                # suggest_reuse or deny
                if self.verbose:
                    print(f"⚠️  {decision['reason']}")

                # For now, create anyway (could prompt user here)
                if decision.get('similar_agents'):
                    # Reuse the suggested agent
                    similar_agent, similarity = decision['similar_agents'][0]
                    agents_to_use.append(similar_agent)
                    metadata['agents_reused'] += 1

        # Step 4: Mark agents as HOT (actively used)
        for agent in agents_to_use:
            self.lifecycle_manager.mark_hot(agent.agent_id)

            # Update last_used
            if agent.agent_id in self.rating_system.performance_profiles:
                profile = self.rating_system.performance_profiles[agent.agent_id]
                profile.last_used = datetime.now()
                self.store.save_performance_profile(profile)

        # Summary
        if self.verbose:
            print(f"\n{'━' * 60}")
            print("📊 ACTIVE ROSTER:")
            for agent in agents_to_use:
                profile = self.rating_system.performance_profiles.get(agent.agent_id)
                rank_icon = profile.current_rank.icon if profile else "📗"
                rank_name = profile.current_rank.display_name if profile else "NOVICE"
                status = "NEW" if metadata['agents_created'] > 0 and agent == agents_to_use[-1] else "CACHED"
                print(f"  {agent.domain.icon} {agent.name} [{status} - {rank_icon} {rank_name}]")

            print(f"\nCreation Cost: ${metadata['creation_cost']:.4f} | "
                  f"Cache Savings: ${metadata['cache_savings']:.4f}")

        return agents_to_use, metadata

    async def rate_agents_interactive(
        self,
        agent_ids: List[str],
        conversation_id: str
    ) -> Dict[str, bool]:
        """
        Interactive rating flow for agents.

        Process:
        1. For each agent, prompt user for rating
        2. Submit rating to rating_system
        3. Check for promotions
        4. Display promotion announcements
        5. Save performance profiles
        6. Update lifecycle tiers

        Args:
            agent_ids: List of agent IDs to rate
            conversation_id: Unique ID for this conversation

        Returns:
            Dict mapping agent_id to was_promoted (bool)
        """

        promotions = {}

        print(f"\n{'━' * 60}")
        print("📝 Please rate the agents:")
        print(f"{'━' * 60}\n")

        for agent_id in agent_ids:
            agent = self.active_agents.get(agent_id)
            if not agent:
                continue

            # Get rating from user
            ratings = DisplayFormatter.print_rating_prompt(agent.name)

            # Submit rating
            rating, new_rank = self.rating_system.submit_rating(
                agent_id=agent_id,
                agent_name=agent.name,
                conversation_id=conversation_id,
                **ratings
            )

            # Check for promotion
            if new_rank:
                profile = self.rating_system.performance_profiles[agent_id]
                old_rank = AgentRank(new_rank.value - 1) if new_rank.value > 1 else AgentRank.NOVICE

                DisplayFormatter.print_promotion_announcement(
                    agent.name,
                    old_rank,
                    new_rank,
                    profile.promotion_points
                )

                promotions[agent_id] = True
            else:
                promotions[agent_id] = False

            # Save performance profile
            profile = self.rating_system.performance_profiles[agent_id]
            self.store.save_performance_profile(profile)

            # Save rating
            self.store.save_rating(rating)

            # Update lifecycle tier
            self.lifecycle_manager.update_tier(agent_id, self.rating_system)

        return promotions

    def get_leaderboard(self, top_n: int = 10) -> List:
        """
        Get top performing agents.

        Args:
            top_n: Number of top agents to return

        Returns:
            List of AgentPerformanceProfile objects
        """
        return self.rating_system.get_leaderboard(top_n)

    async def cleanup_old_agents(self, dry_run: bool = True) -> List[str]:
        """
        Identify and optionally retire old agents.

        Args:
            dry_run: If True, only identify candidates (don't retire)

        Returns:
            List of agent IDs that were retired (or would be retired)
        """

        candidates = []

        for agent_id, profile in self.rating_system.performance_profiles.items():
            if profile.should_retire():
                candidates.append(agent_id)

                if not dry_run:
                    # Actually retire
                    self.lifecycle_manager.retire_agent(agent_id)

                    # Archive data
                    agent = self.active_agents.get(agent_id)
                    if agent:
                        # Save to archive before removing
                        # (implementation detail - could save to archive folder)
                        pass

                    # Remove from active
                    if agent_id in self.active_agents:
                        del self.active_agents[agent_id]

        return candidates

    def get_statistics(self) -> Dict:
        """Get system statistics"""

        return {
            'total_agents': len(self.active_agents),
            'total_conversations': sum(
                p.total_conversations
                for p in self.rating_system.performance_profiles.values()
            ),
            'total_cost': self.factory.get_total_cost() + sum(
                p.total_cost_usd
                for p in self.rating_system.performance_profiles.values()
            ),
            'avg_rating': sum(
                p.avg_rating
                for p in self.rating_system.performance_profiles.values()
            ) / max(len(self.rating_system.performance_profiles), 1),
            'by_rank': {
                rank.display_name: sum(
                    1 for p in self.rating_system.performance_profiles.values()
                    if p.current_rank == rank
                )
                for rank in AgentRank
            }
        }
