"""
Manual validation demo - Shows complete system working

Run: python examples/demo_full_flow.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_coordinator import EnhancedCoordinator


async def demo():
    """Run complete demonstration of Phase 1 system"""

    print("="*70)
    print("DEMO: Dynamic Multi-Agent System - Phase 1 Complete")
    print("="*70)
    print("\nThis demo shows the complete integrated system:")
    print("• Dynamic agent creation")
    print("• Agent classification and deduplication")
    print("• Multi-agent conversations (simulated)")
    print("• Agent rating and promotion")
    print("• Leaderboard and statistics")
    print("• State persistence")
    print("\n" + "="*70)

    coordinator = EnhancedCoordinator()

    # Demo 1: Simple topic
    print("\n\n" + "="*70)
    print("DEMO 1: Simple Topic - Biology")
    print("="*70)

    await coordinator.run_conversation(
        raw_topic="Tell me about photosynthesis in plants",
        max_turns=5
    )

    input("\n\nPress Enter to continue to Demo 2...")

    # Demo 2: Reuse agent (cache hit)
    print("\n\n" + "="*70)
    print("DEMO 2: Agent Reuse (should be instant)")
    print("="*70)

    await coordinator.run_conversation(
        raw_topic="How does photosynthesis convert sunlight to energy?",
        max_turns=5
    )

    input("\n\nPress Enter to continue to Demo 3...")

    # Demo 3: Complex multi-domain topic
    print("\n\n" + "="*70)
    print("DEMO 3: Complex Multi-Domain Topic")
    print("="*70)

    await coordinator.run_conversation(
        raw_topic="Compare classical computing with quantum computing from computer science and physics perspectives",
        max_turns=10
    )

    # Final summary
    print("\n\n" + "="*70)
    print("DEMO COMPLETE - Final System Status")
    print("="*70)

    stats = coordinator.agent_coordinator.get_statistics()

    print(f"\n📊 System Statistics:")
    print(f"  • Total Agents: {stats['total_agents']}")
    print(f"  • Total Conversations: {stats['total_conversations']}")
    print(f"  • Total Cost: ${stats['total_cost']:.4f}")
    print(f"  • Average Rating: {stats['avg_rating']:.2f}/5.00")

    print(f"\n📈 Agents by Rank:")
    for rank_name, count in stats['by_rank'].items():
        if count > 0:
            print(f"  • {rank_name}: {count}")

    print(f"\n{'='*70}")
    print("🎉 Phase 1 Implementation Complete!")
    print("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
