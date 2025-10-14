#!/usr/bin/env python3
"""
Test Phase 1A - Foundation & Infrastructure

Validates that Sub-Phase 1A is correctly implemented:
1. Directory structure exists
2. Data models work correctly
3. JSON persistence layer functions
4. Configuration is valid
5. Dependencies are installed
"""

import sys
import os
from pathlib import Path
from datetime import datetime


def test_directory_structure():
    """Test that required directories exist."""
    print("🔍 Testing directory structure...")

    required_dirs = [
        'src',
        'data',
        'data/agents',
        'data/ratings',
        'data/conversations'
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"   ✅ {dir_path}/ exists")
        else:
            print(f"   ❌ {dir_path}/ NOT found")
            all_exist = False

    return all_exist


def test_imports():
    """Test that new modules can be imported."""
    print("\n🔍 Testing module imports...")

    try:
        from src.data_models import (
            AgentDomain, AgentTier, AgentRank,
            AgentProfile, ConversationRating, AgentPerformanceProfile
        )
        print("   ✅ src.data_models imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import src.data_models: {e}")
        return False

    try:
        from src.persistence import DataStore
        print("   ✅ src.persistence imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import src.persistence: {e}")
        return False

    # Test numpy (required dependency)
    try:
        import numpy as np
        print("   ✅ numpy imported successfully")
    except ImportError:
        print("   ❌ numpy NOT installed - run: pip install numpy>=1.24.0")
        return False

    return True


def test_data_models():
    """Test that data models work correctly."""
    print("\n🔍 Testing data models...")

    try:
        from src.data_models import (
            AgentDomain, AgentProfile, ConversationRating,
            AgentPerformanceProfile, AgentRank
        )

        # Create a test agent profile
        agent = AgentProfile(
            agent_id="test-ophthalmology-001",
            name="Dr. Vision",
            domain=AgentDomain.MEDICINE,
            primary_class="Ophthalmology",
            subclass="Medicine",
            specialization="Retinal Diseases",
            unique_expertise="Expert in ancient and modern eye diseases, particularly retinal conditions",
            core_skills=["ophthalmology", "retinal diseases", "glaucoma", "cataracts"],
            keywords={"eye", "vision", "retina", "ophthalmology", "glaucoma"},
            system_prompt="You are Dr. Vision, an expert ophthalmologist specializing in retinal diseases.",
            created_at=datetime.now(),
            last_used=datetime.now()
        )

        # Test serialization
        agent_dict = agent.to_dict()
        assert 'agent_id' in agent_dict
        assert 'domain' in agent_dict
        assert agent_dict['domain'] == 'medicine'
        print("   ✅ AgentProfile serialization works")

        # Test deserialization
        agent_restored = AgentProfile.from_dict(agent_dict)
        assert agent_restored.agent_id == agent.agent_id
        assert agent_restored.name == agent.name
        assert agent_restored.domain == agent.domain
        print("   ✅ AgentProfile deserialization works")

        # Create a test rating
        rating = ConversationRating(
            agent_id="test-ophthalmology-001",
            conversation_id="conv-001",
            timestamp=datetime.now(),
            helpfulness=5,
            accuracy=5,
            relevance=4,
            clarity=5,
            collaboration=4,
            overall_score=4.65,
            quality_points=5
        )

        # Test rating serialization
        rating_dict = rating.to_dict()
        assert 'agent_id' in rating_dict
        assert rating_dict['helpfulness'] == 5
        print("   ✅ ConversationRating serialization works")

        # Test performance profile
        perf = AgentPerformanceProfile(
            agent_id="test-ophthalmology-001",
            agent_name="Dr. Vision"
        )
        perf.add_rating(rating)
        assert perf.total_conversations == 1
        assert perf.total_points == 5
        assert perf.current_rank == AgentRank.NOVICE  # 5 points = still novice
        print("   ✅ AgentPerformanceProfile works")

        # Test promotion
        for _ in range(5):
            perf.add_rating(rating)  # Add 5 more ratings (5 points each)
        assert perf.total_points == 30  # 6 ratings * 5 points
        assert perf.current_rank == AgentRank.EXPERT  # 30 points = Expert
        print("   ✅ Agent promotion system works")

        return True

    except Exception as e:
        print(f"   ❌ Data models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_persistence():
    """Test that JSON persistence layer works."""
    print("\n🔍 Testing JSON persistence...")

    try:
        from src.data_models import AgentDomain, AgentProfile
        from src.persistence import DataStore

        # Create data store
        store = DataStore()
        print("   ✅ DataStore initialized")

        # Create test agent
        agent = AgentProfile(
            agent_id="test-persistence-001",
            name="Test Agent",
            domain=AgentDomain.SCIENCE,
            primary_class="Physics",
            subclass="Science",
            specialization="Quantum Computing",
            unique_expertise="Expert in quantum algorithms and quantum error correction",
            core_skills=["quantum mechanics", "algorithms", "error correction"],
            keywords={"quantum", "computing", "algorithms", "physics"},
            system_prompt="You are a quantum computing expert.",
            created_at=datetime.now(),
            last_used=datetime.now()
        )

        # Save agent
        store.save_agent(agent)
        print("   ✅ Agent saved to JSON")

        # Load agent
        loaded = store.load_agent("test-persistence-001")
        assert loaded is not None
        assert loaded.agent_id == agent.agent_id
        assert loaded.name == agent.name
        assert loaded.domain == agent.domain
        print("   ✅ Agent loaded from JSON")

        # Test load all agents
        all_agents = store.load_all_agents()
        assert "test-persistence-001" in all_agents
        print(f"   ✅ Load all agents works (found {len(all_agents)} agent(s))")

        # Clean up test file
        store.delete_agent("test-persistence-001")
        print("   ✅ Agent deletion works")

        return True

    except Exception as e:
        print(f"   ❌ Persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test that config.yaml has new Phase 1 sections."""
    print("\n🔍 Testing config.yaml...")

    try:
        import yaml
        config_path = Path('config.yaml')

        if not config_path.exists():
            print("   ❌ config.yaml not found")
            return False

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check for Phase 1 sections
        required_sections = ['openai', 'agent_factory', 'agent_lifecycle', 'rating', 'taxonomy']
        all_present = True

        for section in required_sections:
            if section in config:
                print(f"   ✅ config.yaml has '{section}' section")
            else:
                print(f"   ❌ config.yaml missing '{section}' section")
                all_present = False

        # Verify specific keys
        if 'openai' in config:
            if config['openai'].get('model') == 'gpt-4o-mini':
                print("   ✅ OpenAI model configured correctly")
            else:
                print("   ⚠️  OpenAI model not set to gpt-4o-mini")

        return all_present

    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False


def test_env_example():
    """Test that .env.example has OPENAI_API_KEY."""
    print("\n🔍 Testing .env.example...")

    try:
        env_example = Path('.env.example')
        if not env_example.exists():
            print("   ❌ .env.example not found")
            return False

        content = env_example.read_text()

        if 'OPENAI_API_KEY' in content:
            print("   ✅ .env.example has OPENAI_API_KEY entry")
            return True
        else:
            print("   ❌ .env.example missing OPENAI_API_KEY entry")
            return False

    except Exception as e:
        print(f"   ❌ .env.example test failed: {e}")
        return False


def test_requirements():
    """Test that requirements.txt has new dependencies."""
    print("\n🔍 Testing requirements.txt...")

    try:
        req_file = Path('requirements.txt')
        if not req_file.exists():
            print("   ❌ requirements.txt not found")
            return False

        content = req_file.read_text()

        has_sklearn = 'scikit-learn' in content
        has_numpy = 'numpy' in content

        if has_sklearn:
            print("   ✅ requirements.txt has scikit-learn")
        else:
            print("   ❌ requirements.txt missing scikit-learn")

        if has_numpy:
            print("   ✅ requirements.txt has numpy")
        else:
            print("   ❌ requirements.txt missing numpy")

        return has_sklearn and has_numpy

    except Exception as e:
        print(f"   ❌ requirements.txt test failed: {e}")
        return False


def main():
    """Run all Sub-Phase 1A tests."""
    print("=" * 70)
    print("🚀 Testing Phase 1A: Foundation & Infrastructure")
    print("=" * 70)

    tests = [
        ("Directory Structure", test_directory_structure),
        ("Module Imports", test_imports),
        ("Data Models", test_data_models),
        ("JSON Persistence", test_persistence),
        ("Config File", test_config),
        (".env.example", test_env_example),
        ("requirements.txt", test_requirements)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   ❌ Unexpected error in {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All Sub-Phase 1A tests passed!")
        print("\n✅ Sub-Phase 1A is complete! You are ready for Sub-Phase 1B.")
        print("\nNext steps:")
        print("  1. Install new dependencies: pip install -r requirements.txt")
        print("  2. Add OPENAI_API_KEY to your .env file")
        print("  3. Proceed to Sub-Phase 1B: Topic Refinement & Classification")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
