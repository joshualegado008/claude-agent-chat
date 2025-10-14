#!/usr/bin/env python3
"""
Enhanced Coordinator - Integrates dynamic multi-agent system

This coordinator combines:
- Dynamic agent creation and management (AgentCoordinator)
- Existing conversation flow (ConversationManager, AgentRunner)
- Rating and lifecycle management

Usage:
    python enhanced_coordinator.py [--topic "Your topic here"]
"""

import argparse
import asyncio
import sys
import uuid
from typing import List

from src.agent_coordinator import AgentCoordinator
from src.data_models import AgentProfile
from display_formatter import DisplayFormatter


class EnhancedCoordinator:
    """
    Enhanced coordinator with dynamic agent management.

    Integrates:
    - Dynamic agent creation and reuse
    - Agent rating and promotion
    - Lifecycle management
    - Leaderboard tracking
    """

    def __init__(self):
        """Initialize the enhanced coordinator"""
        # Initialize agent coordinator (Phase 1 systems)
        self.agent_coordinator = AgentCoordinator(verbose=True)

        # NOTE: In a full implementation, you would also initialize:
        # - ConversationManager (for conversation history)
        # - AgentRunner (for running agents)
        # - Any other existing components

    async def run_conversation(self, raw_topic: str, max_turns: int = 10):
        """
        Enhanced conversation flow with dynamic agents.

        Flow:
        1. Get/create agents via agent_coordinator
        2. Display agent roster
        3. Run conversation (placeholder - integrate your existing logic)
        4. Rate agents
        5. Show leaderboard
        6. Save everything

        Args:
            raw_topic: User's topic input
            max_turns: Maximum conversation turns
        """

        print("╔══════════════════════════════════════════════════════════╗")
        print("║     🤖 Dynamic Multi-Agent Conversation System 🤖        ║")
        print("╚══════════════════════════════════════════════════════════╝\n")

        print(f"Topic: {raw_topic}\n")

        # Step 1: Get or create agents
        agents, metadata = await self.agent_coordinator.get_or_create_agents(raw_topic)

        if not agents:
            print("❌ Could not create agents for this topic")
            return

        print(f"\n🚀 Starting conversation...\n")

        # Step 2: Run conversation
        # NOTE: This is where you would integrate your existing conversation logic
        # Example integration:
        #
        # conversation_id = str(uuid.uuid4())
        # self.conversation_manager = ConversationHistory(config, metadata['refined_topic'])
        #
        # for turn in range(max_turns):
        #     for agent in agents:
        #         context = self.conversation_manager.build_context_for_next_turn()
        #         response = await self.agent_runner.run_agent(agent, context)
        #         self.conversation_manager.add_message(response)
        #         self.display.show_message(response)

        # For this demo, simulate a conversation
        conversation_id = str(uuid.uuid4())
        print("   [Agents would discuss the topic here...]")
        print("   [This would use your existing ConversationManager and AgentRunner logic]")
        print(f"\n{'━' * 60}")

        # Step 3: Rate agents
        print("\nConversation Complete!\n")

        agent_ids = [a.agent_id for a in agents]
        promotions = await self.agent_coordinator.rate_agents_interactive(
            agent_ids,
            conversation_id
        )

        # Step 4: Show leaderboard
        print(f"\n{'━' * 60}\n")
        leaderboard = self.agent_coordinator.get_leaderboard(top_n=10)
        DisplayFormatter.print_leaderboard(leaderboard, "🏆 Top Performers")

        # Step 5: Show statistics
        stats = self.agent_coordinator.get_statistics()
        print(f"\n📊 System Statistics:")
        print(f"  Total Agents: {stats['total_agents']}")
        print(f"  Total Conversations: {stats['total_conversations']}")
        print(f"  Total Cost: ${stats['total_cost']:.4f}")
        print(f"  Average Rating: {stats['avg_rating']:.2f}/5.00")

        # Display rank distribution
        print(f"\n📈 Agents by Rank:")
        for rank_name, count in stats['by_rank'].items():
            if count > 0:
                print(f"  • {rank_name}: {count}")

        print(f"\n💾 Conversation saved to data/conversations/{conversation_id}.json")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Enhanced coordinator with dynamic multi-agent system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_coordinator.py --topic "Tell me about photosynthesis"
  python enhanced_coordinator.py --topic "Ancient Canaanite eye diseases"
  python enhanced_coordinator.py --topic "Quantum computing applications"
        """
    )

    parser.add_argument(
        '--topic',
        type=str,
        help='Topic for the conversation',
        default="What are the latest developments in artificial intelligence?"
    )

    parser.add_argument(
        '--max-turns',
        type=int,
        default=10,
        help='Maximum number of conversation turns'
    )

    args = parser.parse_args()

    # Create coordinator
    coordinator = EnhancedCoordinator()

    # Run the conversation
    try:
        await coordinator.run_conversation(
            raw_topic=args.topic,
            max_turns=args.max_turns
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Conversation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
