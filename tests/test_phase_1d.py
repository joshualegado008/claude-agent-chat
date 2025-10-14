#!/usr/bin/env python3
"""
Test Phase 1D - Rating & Lifecycle System

Comprehensive test suite for:
- Rating submission and weighted score calculation
- Promotion point calculation and automatic promotion
- Tier transitions and lifecycle management
- Retirement eligibility with rank-based protection
- God tier protection
- Leaderboard generation
- Performance metrics
- Persistence layer
- Full integration flow

Run with: pytest tests/test_phase_1d.py -v
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rating_system import (
    RatingSystem, ConversationRating, AgentPerformanceProfile, AgentRank
)
from src.lifecycle_manager import LifecycleManager, AgentTier
from src.persistence import DataStore


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def rating_system():
    """Create a fresh RatingSystem instance for each test."""
    return RatingSystem()


@pytest.fixture
def lifecycle_manager():
    """Create a fresh LifecycleManager instance for each test."""
    return LifecycleManager()


@pytest.fixture
def data_store():
    """Create a DataStore with temporary directory for each test."""
    temp_dir = tempfile.mkdtemp()
    store = DataStore(data_dir=temp_dir)
    yield store
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def perfect_rating_data():
    """Standard perfect rating data."""
    return {
        'helpfulness': 5,
        'accuracy': 5,
        'relevance': 5,
        'clarity': 5,
        'collaboration': 5
    }


# ============================================================================
# Test Category 1: Rating Submission
# ============================================================================

def test_rating_submission_perfect_score(rating_system):
    """Test rating submission with perfect scores (5/5 on all dimensions)."""
    rating, new_rank = rating_system.submit_rating(
        agent_id="test-001",
        agent_name="Test Agent",
        conversation_id="conv-001",
        helpfulness=5,
        accuracy=5,
        relevance=5,
        clarity=5,
        collaboration=5
    )

    assert rating.overall_score() == 5.0, "Perfect rating should score 5.0"
    assert rating.quality_points() == 5, "Perfect rating should give 5 points"


def test_rating_submission_weighted_calculation(rating_system):
    """Test weighted score calculation with mixed values."""
    rating, _ = rating_system.submit_rating(
        agent_id="test-002",
        agent_name="Test Agent",
        conversation_id="conv-002",
        helpfulness=5,  # 30% weight = 1.5
        accuracy=4,     # 25% weight = 1.0
        relevance=4,    # 20% weight = 0.8
        clarity=3,      # 15% weight = 0.45
        collaboration=3 # 10% weight = 0.3
    )
    # Total: 1.5 + 1.0 + 0.8 + 0.45 + 0.3 = 4.05

    score = rating.overall_score()
    assert abs(score - 4.05) < 0.01, f"Expected 4.05, got {score}"


def test_rating_validation_rejects_invalid_values():
    """Test that ratings reject out-of-range values."""
    with pytest.raises(ValueError):
        ConversationRating(
            agent_id="test",
            conversation_id="test",
            timestamp=datetime.now(),
            helpfulness=6,  # Invalid!
            accuracy=5,
            relevance=5,
            clarity=5,
            collaboration=5
        )

    with pytest.raises(ValueError):
        ConversationRating(
            agent_id="test",
            conversation_id="test",
            timestamp=datetime.now(),
            helpfulness=0,  # Invalid!
            accuracy=5,
            relevance=5,
            clarity=5,
            collaboration=5
        )


def test_rating_submission_updates_profile(rating_system):
    """Test that submitting a rating updates the agent's profile."""
    agent_id = "test-003"

    # Submit first rating
    rating_system.submit_rating(
        agent_id=agent_id,
        agent_name="Test Agent",
        conversation_id="conv-001",
        helpfulness=5, accuracy=5, relevance=5, clarity=5, collaboration=5
    )

    profile = rating_system.get_performance_profile(agent_id)
    assert profile is not None
    assert profile.total_conversations == 1
    assert profile.promotion_points == 5
    assert len(profile.ratings) == 1


# ============================================================================
# Test Category 2: Promotion Point Calculation
# ============================================================================

def test_promotion_points_mapping():
    """Test quality points mapping for different score ranges."""
    test_cases = [
        # (helpfulness, accuracy, relevance, clarity, collaboration, expected_points)
        (5, 5, 5, 5, 5, 5),  # 5.0 score -> 5 points
        (5, 5, 5, 4, 4, 4),  # ~4.7 score -> 4 points
        (4, 4, 4, 4, 4, 3),  # 4.0 score -> 3 points
        (4, 3, 3, 3, 3, 2),  # ~3.5 score -> 2 points
        (3, 3, 2, 2, 2, 1),  # ~2.6 score -> 1 point
        (2, 2, 1, 1, 1, 0),  # ~1.6 score -> 0 points
    ]

    for h, a, r, c, col, expected in test_cases:
        rating = ConversationRating(
            agent_id="test",
            conversation_id="test",
            timestamp=datetime.now(),
            helpfulness=h,
            accuracy=a,
            relevance=r,
            clarity=c,
            collaboration=col
        )
        points = rating.quality_points()
        score = rating.overall_score()
        assert points == expected, \
            f"Score {score:.2f} should give {expected} points, got {points}"


def test_promotion_points_accumulation(rating_system):
    """Test that promotion points accumulate correctly."""
    agent_id = "test-004"

    # Submit 3 ratings worth 5, 4, and 3 points
    rating_system.submit_rating(
        agent_id=agent_id, agent_name="Test",
        conversation_id="c1",
        helpfulness=5, accuracy=5, relevance=5, clarity=5, collaboration=5
    )
    rating_system.submit_rating(
        agent_id=agent_id, agent_name="Test",
        conversation_id="c2",
        helpfulness=5, accuracy=5, relevance=4, clarity=4, collaboration=4
    )
    rating_system.submit_rating(
        agent_id=agent_id, agent_name="Test",
        conversation_id="c3",
        helpfulness=4, accuracy=4, relevance=4, clarity=4, collaboration=4
    )

    profile = rating_system.get_performance_profile(agent_id)
    # 5 + 4 + 3 = 12 points
    assert profile.promotion_points >= 10, "Should have at least 10 points"


# ============================================================================
# Test Category 3: Automatic Promotion
# ============================================================================

def test_automatic_promotion_novice_to_competent(rating_system, perfect_rating_data):
    """Test promotion from NOVICE to COMPETENT at 10 points."""
    agent_id = "test-promo-001"

    # Start at NOVICE
    rating_system.submit_rating(
        agent_id=agent_id, agent_name="Test Agent",
        conversation_id="c1", **perfect_rating_data
    )
    profile = rating_system.get_performance_profile(agent_id)
    assert profile.current_rank == AgentRank.NOVICE, "Should start as NOVICE"

    # Add second perfect rating (10 points total) -> should promote
    _, new_rank = rating_system.submit_rating(
        agent_id=agent_id, agent_name="Test Agent",
        conversation_id="c2", **perfect_rating_data
    )

    profile = rating_system.get_performance_profile(agent_id)
    assert profile.current_rank == AgentRank.COMPETENT, "Should promote to COMPETENT at 10 points"
    assert new_rank == AgentRank.COMPETENT, "submit_rating should return new rank"


def test_automatic_promotion_to_expert(rating_system, perfect_rating_data):
    """Test promotion to EXPERT at 25 points."""
    agent_id = "test-promo-002"

    # Add 5 perfect ratings (25 points)
    for i in range(5):
        rating_system.submit_rating(
            agent_id=agent_id, agent_name="Test Agent",
            conversation_id=f"c{i}", **perfect_rating_data
        )

    profile = rating_system.get_performance_profile(agent_id)
    assert profile.current_rank == AgentRank.EXPERT, \
        f"Should be EXPERT at 25 points, got {profile.current_rank.display_name}"
    assert profile.promotion_points == 25


def test_automatic_promotion_to_god_tier(rating_system, perfect_rating_data):
    """Test promotion to GOD_TIER at 200 points."""
    agent_id = "test-promo-god"

    # Add 40 perfect ratings (200 points)
    for i in range(40):
        rating_system.submit_rating(
            agent_id=agent_id, agent_name="God Agent",
            conversation_id=f"c{i}", **perfect_rating_data
        )

    profile = rating_system.get_performance_profile(agent_id)
    assert profile.current_rank == AgentRank.GOD_TIER, "Should be GOD_TIER at 200 points"
    assert profile.hall_of_fame is True, "God tier agents should be in hall of fame"


def test_promotion_history_recorded(rating_system, perfect_rating_data):
    """Test that promotion history is properly recorded."""
    agent_id = "test-promo-003"

    # Get to EXPERT (25 points = 2 promotions)
    for i in range(5):
        rating_system.submit_rating(
            agent_id=agent_id, agent_name="Test Agent",
            conversation_id=f"c{i}", **perfect_rating_data
        )

    profile = rating_system.get_performance_profile(agent_id)
    assert len(profile.promotion_history) == 2, "Should have 2 promotions recorded"

    # Check promotion details
    assert profile.promotion_history[0]['to_rank'] == AgentRank.COMPETENT.value
    assert profile.promotion_history[1]['to_rank'] == AgentRank.EXPERT.value


# ============================================================================
# Test Category 4: Tier Transitions
# ============================================================================

def test_tier_new_agent_is_warm(lifecycle_manager):
    """Test that newly used agents are WARM."""
    tier = lifecycle_manager.determine_tier(
        agent_id="test-tier-001",
        last_used=datetime.now(),
        current_rank=AgentRank.NOVICE
    )
    assert tier == AgentTier.WARM


def test_tier_transition_to_cold(lifecycle_manager):
    """Test transition to COLD after 8 days."""
    tier = lifecycle_manager.determine_tier(
        agent_id="test-tier-002",
        last_used=datetime.now() - timedelta(days=8),
        current_rank=AgentRank.NOVICE
    )
    assert tier == AgentTier.COLD, "8 days unused should be COLD"


def test_tier_transition_to_archived(lifecycle_manager):
    """Test transition to ARCHIVED after 91 days."""
    tier = lifecycle_manager.determine_tier(
        agent_id="test-tier-003",
        last_used=datetime.now() - timedelta(days=91),
        current_rank=AgentRank.NOVICE
    )
    assert tier == AgentTier.ARCHIVED, "91 days unused should be ARCHIVED"


def test_tier_hot_agent_stays_hot(lifecycle_manager):
    """Test that HOT agents stay HOT regardless of last_used."""
    agent_id = "test-tier-hot"

    # Mark as hot
    lifecycle_manager.mark_hot(agent_id)

    # Even if last used was long ago, should still be HOT
    tier = lifecycle_manager.determine_tier(
        agent_id=agent_id,
        last_used=datetime.now() - timedelta(days=100),
        current_rank=AgentRank.NOVICE
    )
    assert tier == AgentTier.HOT


def test_tier_mark_inactive_returns_to_warm(lifecycle_manager):
    """Test that marking agent inactive returns it to WARM."""
    agent_id = "test-tier-inactive"

    lifecycle_manager.mark_hot(agent_id)
    assert agent_id in lifecycle_manager.hot_agents

    lifecycle_manager.mark_inactive(agent_id)
    assert agent_id not in lifecycle_manager.hot_agents
    assert lifecycle_manager.get_tier(agent_id) == AgentTier.WARM


def test_tier_transition_history_recorded(lifecycle_manager):
    """Test that tier transitions are recorded in history."""
    agent_id = "test-tier-history"

    lifecycle_manager.mark_hot(agent_id)
    lifecycle_manager.mark_inactive(agent_id)

    history = lifecycle_manager.get_transition_history(agent_id=agent_id)
    assert len(history) >= 2, "Should have at least 2 transitions recorded"


# ============================================================================
# Test Category 5: Retirement Eligibility
# ============================================================================

def test_retirement_novice_protected_7_days(lifecycle_manager):
    """Test NOVICE agents have 7 day protection."""
    # 7 days - should NOT be eligible
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-001",
        last_used=datetime.now() - timedelta(days=7),
        current_rank=AgentRank.NOVICE
    )
    assert not result['eligible'], "NOVICE at 7 days should still be protected"

    # 8 days - should be eligible
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-002",
        last_used=datetime.now() - timedelta(days=8),
        current_rank=AgentRank.NOVICE
    )
    assert result['eligible'], "NOVICE at 8 days should be eligible"


def test_retirement_competent_protected_30_days(lifecycle_manager):
    """Test COMPETENT agents have 30 day protection."""
    # 30 days - should NOT be eligible
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-003",
        last_used=datetime.now() - timedelta(days=30),
        current_rank=AgentRank.COMPETENT
    )
    assert not result['eligible'], "COMPETENT at 30 days should still be protected"

    # 31 days - should be eligible
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-004",
        last_used=datetime.now() - timedelta(days=31),
        current_rank=AgentRank.COMPETENT
    )
    assert result['eligible'], "COMPETENT at 31 days should be eligible"


def test_retirement_expert_protected_90_days(lifecycle_manager):
    """Test EXPERT agents have 90 day protection."""
    # 90 days - should NOT be eligible
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-005",
        last_used=datetime.now() - timedelta(days=90),
        current_rank=AgentRank.EXPERT
    )
    assert not result['eligible'], "EXPERT at 90 days should still be protected"

    # 91 days - should be eligible
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-006",
        last_used=datetime.now() - timedelta(days=91),
        current_rank=AgentRank.EXPERT
    )
    assert result['eligible'], "EXPERT at 91 days should be eligible"


def test_retirement_master_protected_180_days(lifecycle_manager):
    """Test MASTER agents have 180 day protection."""
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-007",
        last_used=datetime.now() - timedelta(days=181),
        current_rank=AgentRank.MASTER
    )
    assert result['eligible'], "MASTER at 181 days should be eligible"


def test_retirement_legendary_protected_365_days(lifecycle_manager):
    """Test LEGENDARY agents have 365 day protection."""
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-retire-008",
        last_used=datetime.now() - timedelta(days=366),
        current_rank=AgentRank.LEGENDARY
    )
    assert result['eligible'], "LEGENDARY at 366 days should be eligible"


# ============================================================================
# Test Category 6: God Tier Protection
# ============================================================================

def test_god_tier_never_retires(lifecycle_manager):
    """Test GOD_TIER agents never retire, regardless of inactivity."""
    # Test at 1000 days
    result = lifecycle_manager.check_retirement_eligibility(
        agent_id="test-god-001",
        last_used=datetime.now() - timedelta(days=1000),
        current_rank=AgentRank.GOD_TIER
    )
    assert not result['eligible'], "GOD_TIER should never be eligible"
    assert result['protection_remaining'] == 99999, "Should have infinite protection"


def test_god_tier_should_retire_returns_false(lifecycle_manager):
    """Test _should_retire always returns False for GOD_TIER."""
    should_retire = lifecycle_manager._should_retire(
        agent_id="test-god-002",
        days_unused=10000,
        current_rank=AgentRank.GOD_TIER
    )
    assert not should_retire, "_should_retire should return False for GOD_TIER"


def test_god_tier_hall_of_fame(rating_system, perfect_rating_data):
    """Test that GOD_TIER agents are marked for hall of fame."""
    agent_id = "test-god-hall"

    # Get to god tier (200 points)
    for i in range(40):
        rating_system.submit_rating(
            agent_id=agent_id, agent_name="Hall of Fame Agent",
            conversation_id=f"c{i}", **perfect_rating_data
        )

    profile = rating_system.get_performance_profile(agent_id)
    assert profile.hall_of_fame is True, "GOD_TIER should be in hall of fame"


# ============================================================================
# Test Category 7: Leaderboard Generation
# ============================================================================

def test_leaderboard_sorting(rating_system, perfect_rating_data):
    """Test that leaderboard sorts agents by promotion points."""
    # Create agents with different point totals
    agents = [
        ("agent-a", 6),   # 30 points (EXPERT)
        ("agent-b", 10),  # 50 points (MASTER)
        ("agent-c", 3),   # 15 points (COMPETENT)
        ("agent-d", 5),   # 25 points (EXPERT)
    ]

    for agent_id, rating_count in agents:
        for i in range(rating_count):
            rating_system.submit_rating(
                agent_id=agent_id,
                agent_name=f"Agent {agent_id[-1].upper()}",
                conversation_id=f"{agent_id}-c{i}",
                **perfect_rating_data
            )

    leaderboard = rating_system.get_leaderboard(top_n=3)

    # Should be sorted: agent-b (50), agent-a (30), agent-d (25)
    assert len(leaderboard) == 3
    assert leaderboard[0].agent_id == "agent-b", "Top agent should have most points"
    assert leaderboard[1].agent_id == "agent-a"
    assert leaderboard[2].agent_id == "agent-d"


def test_leaderboard_get_god_tier_agents(rating_system, perfect_rating_data):
    """Test get_god_tier_agents returns only GOD_TIER agents."""
    # Create one god tier agent
    for i in range(40):
        rating_system.submit_rating(
            agent_id="god-agent",
            agent_name="God Agent",
            conversation_id=f"c{i}",
            **perfect_rating_data
        )

    # Create one non-god tier agent
    rating_system.submit_rating(
        agent_id="normal-agent",
        agent_name="Normal Agent",
        conversation_id="c1",
        **perfect_rating_data
    )

    god_tier_agents = rating_system.get_god_tier_agents()
    assert len(god_tier_agents) == 1
    assert god_tier_agents[0].agent_id == "god-agent"
    assert god_tier_agents[0].current_rank == AgentRank.GOD_TIER


def test_leaderboard_statistics(rating_system, perfect_rating_data):
    """Test get_statistics returns correct aggregate data."""
    # Create 3 agents
    for agent_num in range(3):
        rating_system.submit_rating(
            agent_id=f"stats-agent-{agent_num}",
            agent_name=f"Agent {agent_num}",
            conversation_id=f"c{agent_num}",
            **perfect_rating_data
        )

    stats = rating_system.get_statistics()
    assert stats['total_agents'] == 3
    assert stats['total_ratings'] == 3
    assert 'rank_distribution' in stats
    assert stats['rank_distribution']['Novice'] == 3


# ============================================================================
# Test Category 8: Performance Metrics
# ============================================================================

def test_performance_avg_rating_calculation():
    """Test average rating calculation across multiple ratings."""
    profile = AgentPerformanceProfile(
        agent_id="metrics-001",
        agent_name="Test Metrics"
    )

    # Add ratings: 5.0, 4.0, 4.5
    ratings = [
        (5, 5, 5, 5, 5),  # 5.0
        (4, 4, 4, 4, 4),  # 4.0
        (5, 5, 4, 4, 4),  # ~4.5
    ]

    for h, a, r, c, col in ratings:
        rating = ConversationRating(
            agent_id="metrics-001",
            conversation_id=f"c{h}",
            timestamp=datetime.now(),
            helpfulness=h, accuracy=a, relevance=r, clarity=c, collaboration=col
        )
        profile.add_rating(rating)

    # Average should be around 4.5
    assert 4.4 <= profile.avg_rating <= 4.6, f"Expected ~4.5, got {profile.avg_rating}"


def test_performance_best_worst_tracking():
    """Test that best and worst ratings are tracked."""
    profile = AgentPerformanceProfile(
        agent_id="metrics-002",
        agent_name="Test Metrics"
    )

    # Add varied ratings
    ratings = [(5, 5, 5, 5, 5), (3, 3, 3, 3, 3), (4, 4, 4, 4, 4)]

    for h, a, r, c, col in ratings:
        rating = ConversationRating(
            agent_id="metrics-002",
            conversation_id=f"c{h}",
            timestamp=datetime.now(),
            helpfulness=h, accuracy=a, relevance=r, clarity=c, collaboration=col
        )
        profile.add_rating(rating)

    assert profile.best_rating == 5.0
    assert profile.worst_rating == 3.0


def test_performance_cost_per_value():
    """Test cost_per_value calculation."""
    profile = AgentPerformanceProfile(
        agent_id="metrics-003",
        agent_name="Cost Test"
    )

    # Add rating (5 points)
    rating = ConversationRating(
        agent_id="metrics-003",
        conversation_id="c1",
        timestamp=datetime.now(),
        helpfulness=5, accuracy=5, relevance=5, clarity=5, collaboration=5
    )
    profile.add_rating(rating)

    # Set cost
    profile.total_cost_usd = 0.010  # $0.01 for 5 points

    cost_per_value = profile.cost_per_value()
    expected = 0.010 / 5  # $0.002 per point
    assert abs(cost_per_value - expected) < 0.0001


def test_performance_total_conversations():
    """Test that total conversations are tracked correctly."""
    profile = AgentPerformanceProfile(
        agent_id="metrics-004",
        agent_name="Conversations Test"
    )

    for i in range(5):
        rating = ConversationRating(
            agent_id="metrics-004",
            conversation_id=f"c{i}",
            timestamp=datetime.now(),
            helpfulness=5, accuracy=5, relevance=5, clarity=5, collaboration=5
        )
        profile.add_rating(rating)

    assert profile.total_conversations == 5


# ============================================================================
# Test Category 9: Persistence
# ============================================================================

def test_persistence_save_and_load_profile(data_store, perfect_rating_data):
    """Test saving and loading performance profiles."""
    rating_system = RatingSystem()

    # Create profile with ratings
    agent_id = "persist-001"
    for i in range(3):
        rating_system.submit_rating(
            agent_id=agent_id,
            agent_name="Persist Test",
            conversation_id=f"c{i}",
            **perfect_rating_data
        )

    profile = rating_system.get_performance_profile(agent_id)
    original_points = profile.promotion_points
    original_rank = profile.current_rank

    # Save
    data_store.save_performance_profile(profile)

    # Load
    loaded = data_store.load_performance_profile(agent_id)

    assert loaded is not None
    assert loaded.promotion_points == original_points
    assert loaded.current_rank == original_rank
    assert len(loaded.ratings) == 3


def test_persistence_load_all_profiles(data_store):
    """Test loading all performance profiles."""
    # Create multiple profiles
    for i in range(3):
        profile = AgentPerformanceProfile(
            agent_id=f"persist-multi-{i}",
            agent_name=f"Agent {i}"
        )
        data_store.save_performance_profile(profile)

    all_profiles = data_store.load_all_performance_profiles()
    assert len(all_profiles) >= 3


def test_persistence_delete_profile(data_store):
    """Test deleting performance profiles."""
    profile = AgentPerformanceProfile(
        agent_id="persist-delete",
        agent_name="Delete Test"
    )
    data_store.save_performance_profile(profile)

    # Verify exists
    loaded = data_store.load_performance_profile("persist-delete")
    assert loaded is not None

    # Delete
    result = data_store.delete_performance_profile("persist-delete")
    assert result is True

    # Verify deleted
    loaded = data_store.load_performance_profile("persist-delete")
    assert loaded is None


def test_persistence_leaderboard_cache(data_store):
    """Test leaderboard caching."""
    leaderboard_data = {
        'top_agents': [
            {'agent_id': 'a1', 'name': 'Agent 1', 'points': 50}
        ],
        'total_agents': 1
    }

    data_store.save_leaderboard(leaderboard_data)

    loaded = data_store.load_leaderboard()
    assert loaded is not None
    assert 'generated_at' in loaded
    assert loaded['total_agents'] == 1


def test_persistence_leaderboard_staleness(data_store):
    """Test leaderboard staleness check."""
    leaderboard_data = {
        'top_agents': [],
        'total_agents': 0
    }

    data_store.save_leaderboard(leaderboard_data)

    # Should not be stale immediately
    is_stale = data_store.is_leaderboard_stale(max_age_seconds=300)
    assert not is_stale

    # Should be stale with 0 second threshold
    is_stale = data_store.is_leaderboard_stale(max_age_seconds=0)
    assert is_stale


# ============================================================================
# Test Category 10: Full Integration
# ============================================================================

def test_full_rating_flow(rating_system, lifecycle_manager, data_store, perfect_rating_data):
    """Test complete end-to-end rating flow."""
    agent_id = "integration-001"

    # Step 1: Register agent
    profile = rating_system.register_agent(agent_id, "Integration Test Agent")
    assert profile.current_rank == AgentRank.NOVICE

    # Step 2: Submit ratings and promote
    for i in range(3):  # 15 points = COMPETENT
        rating, new_rank = rating_system.submit_rating(
            agent_id=agent_id,
            agent_name="Integration Test Agent",
            conversation_id=f"integ-c{i}",
            **perfect_rating_data
        )
        if new_rank:
            assert new_rank == AgentRank.COMPETENT

    profile = rating_system.get_performance_profile(agent_id)
    assert profile.current_rank == AgentRank.COMPETENT
    assert profile.promotion_points == 15

    # Step 3: Lifecycle management
    lifecycle_manager.mark_hot(agent_id)
    assert lifecycle_manager.get_tier(agent_id) == AgentTier.HOT

    lifecycle_manager.mark_inactive(agent_id)
    assert lifecycle_manager.get_tier(agent_id) == AgentTier.WARM

    # Step 4: Retirement check
    retirement = lifecycle_manager.check_retirement_eligibility(
        agent_id,
        datetime.now(),
        profile.current_rank
    )
    assert not retirement['eligible'], "Fresh agent should not be eligible"

    # Step 5: Persistence
    data_store.save_performance_profile(profile)
    loaded = data_store.load_performance_profile(agent_id)
    assert loaded is not None
    assert loaded.promotion_points == profile.promotion_points

    # Step 6: Leaderboard
    leaderboard = rating_system.get_leaderboard(top_n=10)
    assert any(p.agent_id == agent_id for p in leaderboard)

    # Cleanup
    data_store.delete_performance_profile(agent_id)


def test_full_flow_retirement_scenario(rating_system, lifecycle_manager):
    """Test retirement flow for low-rank aged agent."""
    agent_id = "retire-scenario"

    # Create NOVICE agent
    rating_system.submit_rating(
        agent_id=agent_id,
        agent_name="Retire Test",
        conversation_id="c1",
        helpfulness=3, accuracy=3, relevance=3, clarity=3, collaboration=3
    )

    profile = rating_system.get_performance_profile(agent_id)

    # Check after 8 days (NOVICE only has 7 day protection)
    retirement = lifecycle_manager.check_retirement_eligibility(
        agent_id,
        datetime.now() - timedelta(days=8),
        profile.current_rank
    )

    assert retirement['eligible'], "NOVICE at 8 days should be eligible"
    assert retirement['days_unused'] == 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
