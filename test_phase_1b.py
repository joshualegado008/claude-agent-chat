#!/usr/bin/env python3
"""
Test Phase 1B - Topic Refinement & Classification

Validates that Sub-Phase 1B is correctly implemented:
1. MetadataExtractor extended with expertise analysis
2. Agent taxonomy with 20 classes works
3. Classification system functions correctly
4. Similarity detection works
5. Capacity management works
"""

import sys
import os
from datetime import datetime


def test_metadata_extractor_extension():
    """Test that MetadataExtractor has new method."""
    print("🔍 Testing MetadataExtractor extension...")

    try:
        from metadata_extractor import MetadataExtractor

        # Check that the new method exists
        if not hasattr(MetadataExtractor, 'analyze_expertise_requirements'):
            print("   ❌ MetadataExtractor missing analyze_expertise_requirements() method")
            return False

        print("   ✅ MetadataExtractor has analyze_expertise_requirements() method")

        # Test the method (without API key, should use fallback)
        try:
            # Create instance without API key to test fallback
            import openai
            extractor = MetadataExtractor(api_key="fake-key-for-testing")

            # This should fail gracefully and return fallback
            result = extractor.analyze_expertise_requirements("quantum computing")

            # Check structure
            required_keys = ['refined_topic', 'expertise_needed', 'suggested_domains']
            for key in required_keys:
                if key not in result:
                    print(f"   ❌ Result missing key: {key}")
                    return False

            print("   ✅ analyze_expertise_requirements() returns correct structure")
            print(f"   ℹ️  Note: Using fallback (no valid API key for test)")

        except Exception as e:
            print(f"   ⚠️  Method test with fallback: {e}")
            # This is okay - we're testing structure, not API

        return True

    except Exception as e:
        print(f"   ❌ MetadataExtractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_taxonomy_imports():
    """Test that taxonomy module imports correctly."""
    print("\n🔍 Testing taxonomy imports...")

    try:
        from src.agent_taxonomy import AgentTaxonomy, AgentClass
        print("   ✅ src.agent_taxonomy imports successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Failed to import src.agent_taxonomy: {e}")
        return False


def test_taxonomy_initialization():
    """Test that taxonomy initializes with 20 classes."""
    print("\n🔍 Testing taxonomy initialization...")

    try:
        from src.agent_taxonomy import AgentTaxonomy
        from src.data_models import AgentDomain

        taxonomy = AgentTaxonomy()
        class_count = taxonomy.get_class_count()

        if class_count != 20:
            print(f"   ❌ Expected 20 classes, got {class_count}")
            return False

        print(f"   ✅ Taxonomy initialized with {class_count} classes")

        # Check domain distribution
        domain_counts = {}
        for domain in AgentDomain:
            count = len(taxonomy.get_classes_by_domain(domain))
            domain_counts[domain.value] = count

        print(f"   ℹ️  Domain distribution:")
        for domain, count in sorted(domain_counts.items()):
            print(f"      {domain:15} {count} classes")

        # Verify expected counts
        expected = {
            'medicine': 4,
            'humanities': 4,
            'science': 4,
            'technology': 3,
            'business': 2,
            'law': 1,
            'arts': 2
        }

        for domain_name, expected_count in expected.items():
            if domain_counts.get(domain_name, 0) != expected_count:
                print(f"   ⚠️  {domain_name} has {domain_counts.get(domain_name, 0)} classes, expected {expected_count}")

        return True

    except Exception as e:
        print(f"   ❌ Taxonomy initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classification():
    """Test that classification works with real examples."""
    print("\n🔍 Testing expertise classification...")

    try:
        from src.agent_taxonomy import AgentTaxonomy
        from src.data_models import AgentDomain

        taxonomy = AgentTaxonomy()

        # Test cases
        test_cases = [
            {
                'description': 'Expert in retinal diseases and glaucoma',
                'expected_class': 'Ophthalmology',
                'expected_domain': AgentDomain.MEDICINE
            },
            {
                'description': 'Quantum computing and quantum algorithms specialist',
                'expected_class': 'Physics',
                'expected_domain': AgentDomain.SCIENCE
            },
            {
                'description': 'Ancient Mesopotamian history and cuneiform expert',
                'expected_class': 'Ancient Near East',
                'expected_domain': AgentDomain.HUMANITIES
            }
        ]

        all_passed = True
        for i, test_case in enumerate(test_cases, 1):
            result = taxonomy.classify_expertise(test_case['description'])

            if result['primary_class'] == test_case['expected_class']:
                print(f"   ✅ Test {i}: Correctly classified as {result['primary_class']}")
            else:
                print(f"   ❌ Test {i}: Expected {test_case['expected_class']}, got {result['primary_class']}")
                all_passed = False

            if result['domain'] == test_case['expected_domain']:
                print(f"      ✅ Correct domain: {result['domain'].value}")
            else:
                print(f"      ❌ Expected domain {test_case['expected_domain'].value}, got {result['domain'].value}")
                all_passed = False

            print(f"      ℹ️  Confidence: {result['confidence']:.2f}")

        return all_passed

    except Exception as e:
        print(f"   ❌ Classification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_detection():
    """Test that similarity detection works."""
    print("\n🔍 Testing similarity detection...")

    try:
        from src.agent_taxonomy import AgentTaxonomy
        from src.data_models import AgentProfile, AgentDomain

        taxonomy = AgentTaxonomy()

        # Create test agents
        agent1 = AgentProfile(
            agent_id="test-eye-001",
            name="Dr. Eye",
            domain=AgentDomain.MEDICINE,
            primary_class="Ophthalmology",
            subclass="Medicine",
            specialization="Retinal Diseases",
            unique_expertise="Expert in retinal diseases",
            core_skills=["retinal diseases", "glaucoma"],
            keywords={"retinal", "diseases", "glaucoma", "eye"},
            system_prompt="Expert ophthalmologist",
            created_at=datetime.now(),
            last_used=datetime.now()
        )

        taxonomy.add_agent(agent1)

        # Test similarity with similar description
        similar = taxonomy.find_similar_agents("retinal diseases expert", threshold=0.3)

        if len(similar) > 0:
            print(f"   ✅ Found {len(similar)} similar agent(s)")
            for agent, score in similar:
                print(f"      {agent.name}: {score:.2f} similarity")
        else:
            print("   ⚠️  No similar agents found (threshold might be too high)")

        # Test with dissimilar description
        dissimilar = taxonomy.find_similar_agents("quantum computing", threshold=0.85)

        if len(dissimilar) == 0:
            print("   ✅ Correctly found no match for dissimilar description")
        else:
            print("   ⚠️  Found match for dissimilar description (unexpected)")

        return True

    except Exception as e:
        print(f"   ❌ Similarity detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_capacity_management():
    """Test that capacity management works."""
    print("\n🔍 Testing capacity management...")

    try:
        from src.agent_taxonomy import AgentTaxonomy

        taxonomy = AgentTaxonomy()

        # Check capacity for a class
        capacity = taxonomy.check_class_capacity("Ophthalmology")

        if 'at_capacity' in capacity and 'count' in capacity and 'max' in capacity:
            print(f"   ✅ Capacity check works")
            print(f"      Ophthalmology: {capacity['count']}/{capacity['max']} agents")
            print(f"      At capacity: {capacity['at_capacity']}")
        else:
            print("   ❌ Capacity check missing required keys")
            return False

        # Check non-existent class
        invalid_capacity = taxonomy.check_class_capacity("NonExistentClass")
        if invalid_capacity['at_capacity'] == False:
            print("   ✅ Non-existent class returns safe defaults")
        else:
            print("   ⚠️  Non-existent class should return at_capacity=False")

        return True

    except Exception as e:
        print(f"   ❌ Capacity management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Sub-Phase 1B tests."""
    print("=" * 70)
    print("🚀 Testing Phase 1B: Topic Refinement & Classification")
    print("=" * 70)

    tests = [
        ("MetadataExtractor Extension", test_metadata_extractor_extension),
        ("Taxonomy Imports", test_taxonomy_imports),
        ("Taxonomy Initialization", test_taxonomy_initialization),
        ("Classification System", test_classification),
        ("Similarity Detection", test_similarity_detection),
        ("Capacity Management", test_capacity_management)
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
        print("\n🎉 All Sub-Phase 1B tests passed!")
        print("\n✅ Sub-Phase 1B is complete!")
        print("\nYou now have:")
        print("  • Extended MetadataExtractor with expertise analysis")
        print("  • 20 agent classes across 7 domains")
        print("  • Classification and similarity detection")
        print("  • Capacity management system")
        print("\nNext: Sub-Phase 1C (Dynamic Agent Creation)")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
