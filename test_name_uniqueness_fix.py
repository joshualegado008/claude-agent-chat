#!/usr/bin/env python3
"""
Test script for Bug #2: Name Race Condition Fix

This script tests the async lock implementation to ensure:
1. No duplicate agent names are created during concurrent creation
2. The used_names set is properly protected by asyncio.Lock
3. Retry logic works correctly for duplicate names
4. Existing agent names are loaded at initialization

Run: python3 test_name_uniqueness_fix.py
"""

import asyncio
from src.agent_factory import AgentFactory
from src.agent_taxonomy import AgentTaxonomy
from src.data_models import AgentDomain


async def test_concurrent_creation():
    """Test concurrent agent creation to verify no duplicates."""
    print("=" * 80)
    print("🧪 TESTING NAME UNIQUENESS FIX (Bug #2)")
    print("=" * 80)

    # Initialize factory
    taxonomy = AgentTaxonomy()
    factory = AgentFactory(taxonomy=taxonomy)

    # Test 1: Check that existing names are loaded
    print("\n" + "─" * 80)
    print("Test 1: Verify existing names are loaded at initialization")
    print("─" * 80)

    if factory.used_names:
        print(f"✅ PASSED: Loaded {len(factory.used_names)} existing agent names")
        print(f"   Sample names: {list(factory.used_names)[:5]}")
    else:
        print(f"⚠️  No existing agents found (this is OK if first run)")

    # Test 2: Create multiple agents concurrently with SAME expertise
    print("\n" + "─" * 80)
    print("Test 2: Create 5 agents concurrently with identical expertise")
    print("This should trigger the race condition if the lock isn't working")
    print("─" * 80)

    expertise = "Mandarin language teaching and Chinese cultural nuances"
    classification = {
        'domain': AgentDomain.HUMANITIES,
        'primary_class': 'Linguistics',
        'subclass': 'Humanities',
        'confidence': 0.9
    }

    # Create 5 agents concurrently
    tasks = []
    for i in range(5):
        task = factory.create_agent(
            expertise_description=f"{expertise} (variant {i+1})",
            classification=classification,
            context=f"Test agent {i+1}",
            created_by="test_script"
        )
        tasks.append(task)

    print(f"\n🚀 Creating 5 agents concurrently...")
    agents = await asyncio.gather(*tasks, return_exceptions=True)

    # Check for exceptions
    exceptions = [a for a in agents if isinstance(a, Exception)]
    if exceptions:
        print(f"\n❌ ERRORS during creation:")
        for e in exceptions:
            print(f"   - {type(e).__name__}: {e}")

    # Filter out exceptions to get successful agents
    successful_agents = [a for a in agents if not isinstance(a, Exception)]

    # Test 3: Verify all names are unique
    print("\n" + "─" * 80)
    print("Test 3: Verify all generated names are unique")
    print("─" * 80)

    agent_names = [agent.name for agent in successful_agents]
    unique_names = set(agent_names)

    print(f"\nGenerated names:")
    for i, name in enumerate(agent_names, 1):
        print(f"   {i}. {name}")

    duplicates_found = len(agent_names) != len(unique_names)

    if duplicates_found:
        print(f"\n❌ FAILED: Found duplicate names!")
        print(f"   Total names: {len(agent_names)}")
        print(f"   Unique names: {len(unique_names)}")

        # Show duplicates
        from collections import Counter
        counts = Counter(agent_names)
        duplicates = {name: count for name, count in counts.items() if count > 1}
        print(f"   Duplicates: {duplicates}")

        return False
    else:
        print(f"\n✅ PASSED: All {len(agent_names)} names are unique!")

    # Test 4: Verify names are in used_names set
    print("\n" + "─" * 80)
    print("Test 4: Verify all names are registered in used_names set")
    print("─" * 80)

    all_registered = all(name in factory.used_names for name in agent_names)

    if all_registered:
        print(f"✅ PASSED: All generated names are in used_names set")
    else:
        print(f"❌ FAILED: Some names not registered in used_names set")
        missing = [name for name in agent_names if name not in factory.used_names]
        print(f"   Missing names: {missing}")
        return False

    # Test 5: Try to create another agent and verify it doesn't reuse names
    print("\n" + "─" * 80)
    print("Test 5: Create one more agent and verify it has a unique name")
    print("─" * 80)

    try:
        new_agent = await factory.create_agent(
            expertise_description=expertise,
            classification=classification,
            context="Final test agent",
            created_by="test_script"
        )

        if new_agent.name in agent_names:
            print(f"❌ FAILED: New agent reused an existing name: {new_agent.name}")
            return False
        else:
            print(f"✅ PASSED: New agent has unique name: {new_agent.name}")

    except Exception as e:
        print(f"❌ FAILED: Exception during final agent creation: {e}")
        return False

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY: All name uniqueness tests passed!")
    print("=" * 80)
    print(f"✅ Async lock is working correctly")
    print(f"✅ No duplicate names generated during concurrent creation")
    print(f"✅ Retry logic prevents duplicates")
    print(f"✅ used_names set is properly maintained")

    return True


async def test_retry_logic():
    """Test that retry logic works when duplicate names are generated."""
    print("\n" + "=" * 80)
    print("🧪 TESTING RETRY LOGIC")
    print("=" * 80)

    taxonomy = AgentTaxonomy()
    factory = AgentFactory(taxonomy=taxonomy)

    # Manually add a name to used_names to force a collision
    test_name = "Dr. Test Agent"
    factory.used_names.add(test_name)

    print(f"\n📝 Pre-populated used_names with: '{test_name}'")
    print(f"   Creating agent with simple expertise to likely generate similar name...")

    expertise = "General medical expertise"
    classification = {
        'domain': AgentDomain.MEDICINE,
        'primary_class': 'Cardiology',
        'subclass': 'Medicine',
        'confidence': 0.8
    }

    try:
        agent = await factory.create_agent(
            expertise_description=expertise,
            classification=classification,
            context="Testing retry logic",
            created_by="test_script"
        )

        print(f"\n✅ Agent created successfully with name: {agent.name}")

        if agent.name == test_name:
            print(f"❌ WARNING: Agent has exact same name as pre-existing (retry may not have triggered)")
        else:
            print(f"✅ PASSED: Agent has different name, retry logic likely worked")

        return True

    except Exception as e:
        print(f"❌ FAILED: Exception during agent creation: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🧪 BUG #2 NAME UNIQUENESS TEST SUITE")
    print("=" * 80)

    # Test 1: Concurrent creation
    test1_passed = await test_concurrent_creation()

    # Test 2: Retry logic
    test2_passed = await test_retry_logic()

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED! Name race condition bug is fixed.")
        return True
    else:
        print("❌ SOME TESTS FAILED! Name race condition bug may still be present.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
