#!/usr/bin/env python3
"""
Test script for Bug #1: Classification Fallback Fix

This script tests the improved classification system to ensure:
1. No more Cardiology fallback for non-medical topics
2. Proper classification of Mandarin/Chinese/bilingual topics
3. Cultural Studies recognition
4. History recognition
5. Psychology recognition
6. Education recognition
7. Proper medicine classification only when explicitly medical

Run: python3 test_classification_fix.py
"""

from src.agent_taxonomy import AgentTaxonomy
from src.data_models import AgentDomain


def test_classification():
    """Run comprehensive classification tests."""
    print("=" * 80)
    print("🧪 TESTING CLASSIFICATION FIX (Bug #1)")
    print("=" * 80)

    taxonomy = AgentTaxonomy()

    # Test cases with expected results
    test_cases = [
        # 1. Mandarin/Chinese should classify as Linguistics
        {
            "description": "Mandarin language teaching and Chinese cultural nuances",
            "expected_class": "Linguistics",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Mandarin Language Teaching"
        },
        {
            "description": "Chinese language learning and bilingual education",
            "expected_class": "Linguistics",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Bilingual Education"
        },

        # 2. Cultural topics should classify as Cultural Studies
        {
            "description": "Chinese cultural traditions and cross-cultural communication",
            "expected_class": "Cultural Studies",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Cultural Traditions"
        },
        {
            "description": "Intercultural studies and ethnographic research",
            "expected_class": "Cultural Studies",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Intercultural Studies"
        },

        # 3. History should classify correctly
        {
            "description": "Ancient civilizations and historical research methods",
            "expected_class": "History",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Ancient History"
        },
        {
            "description": "Historical analysis of medieval Europe",
            "expected_class": "History",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Medieval History"
        },

        # 4. Psychology should classify correctly
        {
            "description": "Cognitive psychology and behavioral analysis",
            "expected_class": "Psychology",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Cognitive Psychology"
        },
        {
            "description": "Mental health therapy and counseling techniques",
            "expected_class": "Psychology",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Mental Health"
        },

        # 5. Education should classify correctly
        {
            "description": "Curriculum design and pedagogical methods",
            "expected_class": "Education",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Curriculum Design"
        },
        {
            "description": "Teaching strategies and classroom management",
            "expected_class": "Education",
            "expected_domain": AgentDomain.HUMANITIES,
            "name": "Teaching Strategies"
        },

        # 6. Medical topics should ONLY classify as medicine when explicitly medical
        {
            "description": "Cardiac surgery and heart disease treatment",
            "expected_class": "Cardiology",
            "expected_domain": AgentDomain.MEDICINE,
            "name": "Cardiac Surgery"
        },
        {
            "description": "Cancer treatment and oncology research",
            "expected_class": "Oncology",
            "expected_domain": AgentDomain.MEDICINE,
            "name": "Cancer Treatment"
        },

        # 7. Non-medical topics should NEVER classify as Cardiology
        {
            "description": "Software engineering and web development",
            "expected_class": "Software Engineering",
            "expected_domain": AgentDomain.TECHNOLOGY,
            "name": "Web Development"
        },
        {
            "description": "Machine learning and AI algorithms",
            "expected_class": "AI and Machine Learning",
            "expected_domain": AgentDomain.TECHNOLOGY,
            "name": "Machine Learning"
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"Description: {test['description']}")

        result = taxonomy.classify_expertise(test['description'])

        if not result:
            print(f"❌ FAILED: No classification returned (returned None)")
            failed += 1
            continue

        actual_class = result['primary_class']
        actual_domain = result['domain']
        confidence = result['confidence']

        class_match = actual_class == test['expected_class']
        domain_match = actual_domain == test['expected_domain']

        if class_match and domain_match:
            print(f"✅ PASSED")
            print(f"   └─ Class: {actual_class} (confidence: {confidence:.2f})")
            print(f"   └─ Domain: {actual_domain.value}")
            passed += 1
        else:
            print(f"❌ FAILED")
            print(f"   Expected: {test['expected_class']} ({test['expected_domain'].value})")
            print(f"   Got:      {actual_class} ({actual_domain.value}) - confidence: {confidence:.2f}")

            # Check for the specific Cardiology bug
            if actual_class == "Cardiology" and test['expected_domain'] != AgentDomain.MEDICINE:
                print(f"   🚨 BUG DETECTED: Non-medical topic classified as Cardiology!")

            failed += 1

    # Summary
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    print(f"{'=' * 80}")

    if failed == 0:
        print("✅ ALL TESTS PASSED! Classification bug is fixed.")
        return True
    else:
        print(f"❌ {failed} TESTS FAILED! Classification bug still present.")
        return False


if __name__ == "__main__":
    success = test_classification()
    exit(0 if success else 1)
