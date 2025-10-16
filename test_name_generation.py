#!/usr/bin/env python3
"""
Test Script: Name Generation Diversity & Title Distribution

This script verifies that the faker-based name generation:
1. Produces unique names (no duplicates)
2. Shows cultural diversity (multiple locales)
3. Maintains target title distribution (~30% overall)
4. Domain-specific title probabilities are respected
"""

import sys
from collections import Counter
from src.agent_taxonomy import AgentTaxonomy
from src.agent_factory import AgentFactory
from src.data_models import AgentDomain


def test_name_generation():
    """Test faker name generation across all domains."""

    print("=" * 80)
    print("🧪 TESTING NAME GENERATION DIVERSITY")
    print("=" * 80)

    # Initialize factory
    taxonomy = AgentTaxonomy()
    factory = AgentFactory(taxonomy=taxonomy)

    # Test parameters
    NUM_NAMES_PER_DOMAIN = 10
    domains = list(AgentDomain)

    all_names = []
    title_count = 0
    total_count = 0
    domain_stats = {}

    # Generate names for each domain
    for domain in domains:
        print(f"\n{'-' * 80}")
        print(f"Testing {domain.name} ({domain.value})")
        print(f"{'-' * 80}")

        domain_names = []
        domain_titles = 0

        # Create fake classification for testing
        classification = {
            'domain': domain,
            'primary_class': 'Test Class',
            'subclass': 'Test',
            'confidence': 1.0
        }

        for i in range(NUM_NAMES_PER_DOMAIN):
            name = factory._generate_unique_name_with_faker(domain, classification)

            if name:
                domain_names.append(name)
                all_names.append(name)
                total_count += 1

                # Check if name has a title
                has_title = any(title in name for title in ['Dr.', 'Prof.', 'Engineer', 'Researcher',
                                                              'Nurse', 'Practitioner', 'Attorney',
                                                              'Esq.', 'CTO', 'CEO', 'VP', 'Analyst',
                                                              'Maestro', 'Designer', 'Architect'])
                if has_title:
                    title_count += 1
                    domain_titles += 1

                # Print sample (first 5 for brevity)
                if i < 5:
                    title_marker = "📌" if has_title else "  "
                    print(f"  {title_marker} {name}")

        # Domain statistics
        title_pct = (domain_titles / len(domain_names) * 100) if domain_names else 0
        domain_stats[domain.name] = {
            'total': len(domain_names),
            'with_titles': domain_titles,
            'title_percentage': title_pct
        }

        print(f"\n  Domain Summary:")
        print(f"    Generated: {len(domain_names)} names")
        print(f"    With titles: {domain_titles} ({title_pct:.1f}%)")

    # Overall statistics
    print(f"\n{'=' * 80}")
    print(f"📊 OVERALL STATISTICS")
    print(f"{'=' * 80}\n")

    # Uniqueness check
    duplicates = len(all_names) - len(set(all_names))
    print(f"✅ Uniqueness Check:")
    print(f"   Total names generated: {len(all_names)}")
    print(f"   Unique names: {len(set(all_names))}")
    print(f"   Duplicates: {duplicates}")

    if duplicates == 0:
        print(f"   ✅ PASSED: All names are unique!\n")
    else:
        print(f"   ❌ FAILED: Found {duplicates} duplicate names\n")

    # Title distribution
    overall_title_pct = (title_count / total_count * 100) if total_count > 0 else 0
    print(f"📋 Title Distribution:")
    print(f"   Overall: {title_count}/{total_count} ({overall_title_pct:.1f}%)")
    print(f"   Target: ~30%")

    if 20 <= overall_title_pct <= 40:
        print(f"   ✅ PASSED: Within target range (20-40%)\n")
    else:
        print(f"   ⚠️  WARNING: Outside target range\n")

    # Per-domain breakdown
    print(f"📈 Title Distribution by Domain:")
    for domain_name, stats in domain_stats.items():
        pct = stats['title_percentage']
        domain_obj = next((d for d in domains if d.name == domain_name), None)

        # Get expected percentage based on TITLE_CONFIG
        expected_pct = {
            'TECHNOLOGY': 20,
            'MEDICINE': 50,
            'HUMANITIES': 40,
            'SCIENCE': 40,
            'BUSINESS': 25,
            'LAW': 35,
            'ARTS': 15
        }.get(domain_name, 30)

        status = "✅" if abs(pct - expected_pct) < 20 else "⚠️ "
        print(f"   {status} {domain_name:<12} {stats['with_titles']:>2}/{stats['total']:<2} ({pct:>5.1f}%) - Expected: ~{expected_pct}%")

    # Cultural diversity check
    print(f"\n🌍 Cultural Diversity:")
    # Count name origins (simple heuristic: count distinct first/last name patterns)
    first_names = [name.split()[-1] for name in all_names]  # Last word as last name
    unique_last_names = len(set(first_names))
    diversity_score = (unique_last_names / len(all_names) * 100) if all_names else 0

    print(f"   Unique last names: {unique_last_names}/{len(all_names)}")
    print(f"   Diversity score: {diversity_score:.1f}%")

    if diversity_score > 70:
        print(f"   ✅ PASSED: High diversity (>70%)")
    elif diversity_score > 50:
        print(f"   ⚠️  WARNING: Moderate diversity (50-70%)")
    else:
        print(f"   ❌ FAILED: Low diversity (<50%)")

    # Final verdict
    print(f"\n{'=' * 80}")
    print(f"✅ TEST COMPLETE")
    print(f"{'=' * 80}\n")

    success = (duplicates == 0 and 20 <= overall_title_pct <= 40 and diversity_score > 50)

    if success:
        print("✅ ALL CHECKS PASSED!")
        print("   - No duplicate names")
        print("   - Title distribution within target")
        print("   - Good cultural diversity")
        return True
    else:
        print("⚠️  SOME CHECKS FAILED - Review results above")
        return False


if __name__ == "__main__":
    try:
        success = test_name_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
