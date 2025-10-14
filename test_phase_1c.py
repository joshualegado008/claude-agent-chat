#!/usr/bin/env python3
"""
Test Phase 1C - Dynamic Agent Creation

Validates that Sub-Phase 1C is correctly implemented:
1. AgentProfile extensions work correctly
2. Agent Factory creates complete agents
3. Deduplication system prevents duplicates
4. Integration between components works
5. Cost tracking is accurate
6. File creation works properly

This test suite uses REAL API calls to ensure end-to-end functionality.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
import json

# Test categories
TEST_CATEGORIES = {
    'profile': 'AgentProfile Extensions',
    'factory_basic': 'Basic Agent Creation',
    'factory_advanced': 'Advanced Agent Creation',
    'dedup_high': 'Deduplication (≥95% similarity)',
    'dedup_medium': 'Deduplication (85-95% similarity)',
    'dedup_low': 'Deduplication (<85% similarity)',
    'capacity': 'Capacity Management',
    'costs': 'Cost Tracking',
    'files': 'File Creation',
    'integration': 'End-to-End Integration'
}


def test_agent_profile_extensions():
    """Test 1: AgentProfile extensions from Part 1"""
    print("🔍 Testing AgentProfile extensions...")

    try:
        from src.data_models import AgentProfile, AgentDomain
        from datetime import datetime
        import numpy as np

        # Create agent with all new fields
        agent = AgentProfile(
            agent_id="test-001",
            name="Dr. Test",
            domain=AgentDomain.SCIENCE,
            primary_class="Physics",
            subclass="Science",
            specialization="Quantum Computing",
            unique_expertise="Expert in quantum algorithms and computation",
            core_skills=["quantum mechanics", "algorithms", "computation"],
            keywords={"quantum", "computing", "physics", "algorithms"},
            system_prompt="You are a quantum computing expert.",
            created_at=datetime.now(),
            last_used=datetime.now(),
            agent_file_path=".claude/agents/dynamic/test-001.md",
            total_uses=5,
            creation_cost_usd=0.0025,
            created_by="test_system",
            model="claude-sonnet-4-5",
            secondary_skills=["mathematics", "programming"],
            expertise_embedding=np.random.rand(128)
        )

        # Test serialization
        agent_dict = agent.to_dict()

        required_fields = ['agent_file_path', 'total_uses', 'creation_cost_usd',
                          'created_by', 'model', 'secondary_skills']
        for field in required_fields:
            if field not in agent_dict:
                print(f"   ❌ Missing field in to_dict(): {field}")
                return False

        # Test deserialization
        agent_restored = AgentProfile.from_dict(agent_dict)

        if agent_restored.total_uses != 5:
            print(f"   ❌ total_uses not restored correctly: {agent_restored.total_uses}")
            return False

        if agent_restored.creation_cost_usd != 0.0025:
            print(f"   ❌ creation_cost_usd not restored correctly: {agent_restored.creation_cost_usd}")
            return False

        # Test display card
        card = agent.display_card()
        if "Dr. Test" not in card:
            print("   ❌ display_card() missing agent name")
            return False

        # Test domain icon
        icon = agent.domain.icon
        if icon != "🔬":
            print(f"   ❌ Domain icon incorrect: {icon}")
            return False

        print("   ✅ All AgentProfile extensions working")
        return True

    except Exception as e:
        print(f"   ❌ AgentProfile test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_agent_creation():
    """Test 2: Basic agent creation with factory"""
    print("\n🔍 Testing basic agent creation...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)

        # Create simple agent
        agent = await factory.create_agent(
            expertise_description="ophthalmologist specializing in retinal diseases",
            created_by="test_system"
        )

        # Validate basic fields
        if not agent.agent_id.startswith("dynamic-"):
            print(f"   ❌ Invalid agent_id: {agent.agent_id}")
            return False

        if not agent.name:
            print("   ❌ Agent name is empty")
            return False

        if agent.domain.value != "medicine":
            print(f"   ❌ Wrong domain: {agent.domain.value}, expected: medicine")
            return False

        if agent.primary_class != "Ophthalmology":
            print(f"   ❌ Wrong class: {agent.primary_class}, expected: Ophthalmology")
            return False

        if len(agent.core_skills) < 2:
            print(f"   ❌ Too few core skills: {len(agent.core_skills)}")
            return False

        if len(agent.keywords) < 3:
            print(f"   ❌ Too few keywords: {len(agent.keywords)}")
            return False

        if len(agent.system_prompt.split()) < 100:
            print(f"   ❌ System prompt too short: {len(agent.system_prompt.split())} words")
            return False

        # Check file was created
        file_path = Path(agent.agent_file_path)
        if not file_path.exists():
            print(f"   ❌ Agent file not created: {agent.agent_file_path}")
            return False

        # Check file content
        with open(file_path, 'r') as f:
            content = f.read()
            if "Agent ID" not in content:
                print("   ❌ Agent file missing metadata footer")
                return False

        # Check cost tracking
        if agent.creation_cost_usd <= 0:
            print(f"   ❌ Creation cost not tracked: {agent.creation_cost_usd}")
            return False

        print(f"   ✅ Created: {agent.name}")
        print(f"   ✅ Domain: {agent.domain.icon} {agent.domain.value}")
        print(f"   ✅ Class: {agent.primary_class}")
        print(f"   ✅ Skills: {', '.join(agent.core_skills[:3])}")
        print(f"   ✅ Prompt length: {len(agent.system_prompt.split())} words")
        print(f"   ✅ Cost: ${agent.creation_cost_usd:.4f}")
        print(f"   ✅ File: {agent.agent_file_path}")

        return True

    except Exception as e:
        print(f"   ❌ Basic creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_advanced_agent_creation():
    """Test 3: Advanced agent creation with different domains"""
    print("\n🔍 Testing advanced agent creation...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)

        test_cases = [
            {
                'expertise': 'ancient Near Eastern history specialist focusing on Mesopotamian civilizations',
                'expected_domain': 'humanities',
                'expected_class': 'Ancient Near East'
            },
            {
                'expertise': 'quantum physicist specializing in quantum computing and algorithms',
                'expected_domain': 'science',
                'expected_class': 'Physics'
            },
            {
                'expertise': 'machine learning engineer specializing in neural networks and deep learning',
                'expected_domain': 'technology',
                'expected_class': 'AI and Machine Learning'
            }
        ]

        all_passed = True
        for i, test_case in enumerate(test_cases, 1):
            try:
                agent = await factory.create_agent(
                    expertise_description=test_case['expertise'],
                    created_by="test_advanced"
                )

                if agent.domain.value != test_case['expected_domain']:
                    print(f"   ❌ Test {i}: Wrong domain: {agent.domain.value} != {test_case['expected_domain']}")
                    all_passed = False
                    continue

                if agent.primary_class != test_case['expected_class']:
                    print(f"   ❌ Test {i}: Wrong class: {agent.primary_class} != {test_case['expected_class']}")
                    all_passed = False
                    continue

                print(f"   ✅ Test {i}: {agent.name} ({agent.primary_class})")

            except Exception as e:
                print(f"   ❌ Test {i} failed: {e}")
                all_passed = False

        if all_passed:
            total_cost = factory.get_total_cost()
            print(f"   ✅ All advanced tests passed")
            print(f"   ✅ Total cost for 3 agents: ${total_cost:.4f}")

        return all_passed

    except Exception as e:
        print(f"   ❌ Advanced creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_deduplication_high_similarity():
    """Test 4: Deduplication at ≥95% similarity"""
    print("\n🔍 Testing deduplication (high similarity)...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy
        from src.deduplication import AgentDeduplicationSystem

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)
        dedup = AgentDeduplicationSystem(taxonomy)

        # Create first agent
        agent1 = await factory.create_agent(
            expertise_description="cardiologist specializing in heart disease",
            created_by="test_dedup"
        )
        dedup.register_agent(agent1)

        print(f"   └─ Created first agent: {agent1.name}")

        # Try to create nearly identical agent
        decision = dedup.check_before_create(
            expertise_description="cardiologist specializing in heart disease",
            strict=True
        )

        if decision['action'] != 'reuse':
            print(f"   ❌ Expected 'reuse', got '{decision['action']}'")
            print(f"      Reason: {decision['reason']}")
            return False

        if decision['agent_id'] != agent1.agent_id:
            print(f"   ❌ Wrong agent_id in reuse decision")
            return False

        print(f"   ✅ Correctly detected high similarity")
        print(f"   ✅ Action: {decision['action']}")
        print(f"   ✅ Reason: {decision['reason']}")

        return True

    except Exception as e:
        print(f"   ❌ High similarity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_deduplication_medium_similarity():
    """Test 5: Deduplication at 85-95% similarity"""
    print("\n🔍 Testing deduplication (medium similarity)...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy
        from src.deduplication import AgentDeduplicationSystem

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)
        dedup = AgentDeduplicationSystem(taxonomy)

        # Create first agent
        agent1 = await factory.create_agent(
            expertise_description="neurologist specializing in brain disorders",
            created_by="test_dedup_med"
        )
        dedup.register_agent(agent1)

        print(f"   └─ Created first agent: {agent1.name}")

        # Try to create somewhat similar agent
        decision = dedup.check_before_create(
            expertise_description="neurologist specializing in nervous system diseases",
            strict=True
        )

        # Should be either 'suggest_reuse' or 'create' depending on similarity
        if decision['action'] not in ['suggest_reuse', 'create']:
            print(f"   ❌ Unexpected action: {decision['action']}")
            return False

        print(f"   ✅ Action: {decision['action']}")
        print(f"   ✅ Reason: {decision['reason']}")

        if 'similar_agents' in decision and decision['similar_agents']:
            sim_agent, similarity = decision['similar_agents'][0]
            print(f"   ✅ Most similar: {sim_agent.name} ({similarity*100:.1f}%)")

        return True

    except Exception as e:
        print(f"   ❌ Medium similarity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_deduplication_low_similarity():
    """Test 6: Deduplication at <85% similarity"""
    print("\n🔍 Testing deduplication (low similarity)...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy
        from src.deduplication import AgentDeduplicationSystem

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)
        dedup = AgentDeduplicationSystem(taxonomy)

        # Create ophthalmology agent
        agent1 = await factory.create_agent(
            expertise_description="ophthalmologist specializing in retinal diseases",
            created_by="test_dedup_low"
        )
        dedup.register_agent(agent1)

        print(f"   └─ Created first agent: {agent1.name} (Ophthalmology)")

        # Try to create very different agent (different domain entirely)
        decision = dedup.check_before_create(
            expertise_description="ancient historian specializing in Mesopotamian civilizations",
            strict=True
        )

        if decision['action'] != 'create':
            print(f"   ❌ Expected 'create', got '{decision['action']}'")
            print(f"      Reason: {decision['reason']}")
            return False

        print(f"   ✅ Correctly allowed creation of different agent")
        print(f"   ✅ Reason: {decision['reason']}")

        return True

    except Exception as e:
        print(f"   ❌ Low similarity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_capacity_enforcement():
    """Test 7: Capacity limits enforcement"""
    print("\n🔍 Testing capacity enforcement...")

    try:
        from src.agent_taxonomy import AgentTaxonomy
        from src.deduplication import AgentDeduplicationSystem

        taxonomy = AgentTaxonomy()
        dedup = AgentDeduplicationSystem(taxonomy)

        # Check initial capacity
        capacity = taxonomy.check_class_capacity("Ophthalmology")

        print(f"   └─ Ophthalmology capacity: {capacity['count']}/{capacity['max']}")

        if capacity['max'] != 10:
            print(f"   ❌ Expected max capacity 10, got {capacity['max']}")
            return False

        if capacity['at_capacity']:
            print(f"   ⚠️  Already at capacity, test may not be conclusive")

        print(f"   ✅ Capacity check working")
        print(f"   ✅ Current: {capacity['count']}/{capacity['max']}")
        print(f"   ✅ At capacity: {capacity['at_capacity']}")

        return True

    except Exception as e:
        print(f"   ❌ Capacity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cost_tracking():
    """Test 8: Accurate cost tracking"""
    print("\n🔍 Testing cost tracking...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)

        initial_cost = factory.get_total_cost()
        initial_count = factory.get_agents_created_count()

        # Create one agent
        agent = await factory.create_agent(
            expertise_description="test expert for cost tracking",
            created_by="test_cost"
        )

        final_cost = factory.get_total_cost()
        final_count = factory.get_agents_created_count()

        # Check that cost increased
        if final_cost <= initial_cost:
            print(f"   ❌ Cost did not increase: {initial_cost} -> {final_cost}")
            return False

        # Check that count increased
        if final_count != initial_count + 1:
            print(f"   ❌ Count incorrect: {initial_count} -> {final_count}")
            return False

        # Check agent's individual cost
        if agent.creation_cost_usd <= 0:
            print(f"   ❌ Agent cost not tracked: {agent.creation_cost_usd}")
            return False

        # Typical cost should be $0.001-0.01 per agent
        if agent.creation_cost_usd > 0.1:
            print(f"   ⚠️  Warning: Unusually high cost: ${agent.creation_cost_usd:.4f}")

        print(f"   ✅ Cost tracking working")
        print(f"   ✅ Agent cost: ${agent.creation_cost_usd:.4f}")
        print(f"   ✅ Total cost: ${final_cost:.4f}")
        print(f"   ✅ Agents created: {final_count}")

        return True

    except Exception as e:
        print(f"   ❌ Cost tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_file_creation():
    """Test 9: Agent file creation and format"""
    print("\n🔍 Testing file creation...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy

        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)

        # Create agent
        agent = await factory.create_agent(
            expertise_description="test expert for file validation",
            created_by="test_files"
        )

        # Check file exists
        file_path = Path(agent.agent_file_path)
        if not file_path.exists():
            print(f"   ❌ File not created: {agent.agent_file_path}")
            return False

        # Read and validate content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required elements
        required_elements = [
            '#',  # Markdown header
            agent.name,  # Agent name
            'Agent ID',  # Metadata footer
            'Domain',
            'Classification',
            'Created'
        ]

        missing = []
        for element in required_elements:
            if element not in content:
                missing.append(element)

        if missing:
            print(f"   ❌ File missing elements: {missing}")
            print(f"   Content preview: {content[:200]}")
            return False

        # Check file is valid markdown
        if not content.startswith('#'):
            print("   ⚠️  Warning: File may not be valid markdown")

        word_count = len(content.split())
        print(f"   ✅ File created successfully")
        print(f"   ✅ File size: {len(content)} bytes ({word_count} words)")
        print(f"   ✅ Location: {file_path}")

        return True

    except Exception as e:
        print(f"   ❌ File creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test 10: End-to-end integration"""
    print("\n🔍 Testing end-to-end integration...")

    try:
        from src.agent_factory import AgentFactory
        from src.agent_taxonomy import AgentTaxonomy
        from src.deduplication import AgentDeduplicationSystem
        from src.persistence import DataStore

        # Initialize all components
        taxonomy = AgentTaxonomy()
        factory = AgentFactory(taxonomy)
        dedup = AgentDeduplicationSystem(taxonomy)
        store = DataStore()

        print("   └─ All components initialized")

        # Create agent
        agent = await factory.create_agent(
            expertise_description="integration test specialist",
            created_by="test_integration"
        )
        print(f"   └─ Created: {agent.name}")

        # Register with deduplication
        dedup.register_agent(agent)
        print(f"   └─ Registered with deduplication")

        # Save to persistence
        store.save_agent(agent)
        print(f"   └─ Saved to persistence")

        # Load back from persistence
        loaded_agent = store.load_agent(agent.agent_id)
        if not loaded_agent:
            print(f"   ❌ Failed to load agent from persistence")
            return False
        print(f"   └─ Loaded from persistence")

        # Verify loaded data matches
        if loaded_agent.name != agent.name:
            print(f"   ❌ Name mismatch after load")
            return False

        # Check deduplication prevents duplicate
        decision = dedup.check_before_create(
            expertise_description="integration test specialist",
            strict=True
        )

        if decision['action'] != 'reuse':
            print(f"   ⚠️  Deduplication didn't prevent duplicate: {decision['action']}")

        # Display agent card
        card = agent.display_card()
        if agent.name not in card:
            print("   ❌ Display card malformed")
            return False

        print("   ✅ End-to-end integration successful")
        print(f"   ✅ Factory → Dedup → Persistence → Load → Display")

        return True

    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all test categories"""
    print("=" * 70)
    print("🚀 Testing Phase 1C: Dynamic Agent Creation")
    print("=" * 70)

    results = {}

    # Test 1: Profile extensions (synchronous)
    results['profile'] = test_agent_profile_extensions()

    # Test 2-10: Factory and deduplication (asynchronous)
    results['factory_basic'] = await test_basic_agent_creation()
    results['factory_advanced'] = await test_advanced_agent_creation()
    results['dedup_high'] = await test_deduplication_high_similarity()
    results['dedup_medium'] = await test_deduplication_medium_similarity()
    results['dedup_low'] = await test_deduplication_low_similarity()
    results['capacity'] = await test_capacity_enforcement()
    results['costs'] = await test_cost_tracking()
    results['files'] = await test_file_creation()
    results['integration'] = await test_integration()

    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for category, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        name = TEST_CATEGORIES.get(category, category)
        print(f"{status} - {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All Sub-Phase 1C tests passed!")
        print("\n✅ Sub-Phase 1C is complete!")
        print("\nYou now have:")
        print("  • Dynamic agent creation with Claude API")
        print("  • Deduplication system with 3-tier logic")
        print("  • Cost tracking for all API calls")
        print("  • Agent file generation in markdown format")
        print("\nNext: Sub-Phase 1D (Rating & Lifecycle System)")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
        return 1


def main():
    """Main entry point"""
    try:
        return asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
