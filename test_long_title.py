#!/usr/bin/env python3
"""
Test script to verify that long conversation titles work correctly.

This tests the original failing title that caused the bug.
"""

import sys
from db_manager import DatabaseManager

def test_long_title():
    """Test creating a conversation with a long title (313 chars)."""

    # Original failing title that caused the bug
    long_title = (
        "recently we have seen research on jailbreaking LLM's and context poisoniong, "
        "reference: https://icml.cc/virtual/2025/poster/45356 and "
        "https://www.anthropic.com/research/small-samples-poison. debate the issue and "
        "how we can prevent and mitigate this going forward, using established cyber "
        "security principles for software."
    )

    print("="*60)
    print("Testing Long Title Fix")
    print("="*60)
    print(f"\nOriginal title length: {len(long_title)} characters")
    print(f"Title: {long_title[:100]}...\n")

    try:
        # Initialize database manager
        print("1. Connecting to database...")
        db = DatabaseManager()
        print("   ✓ Connected\n")

        # Try to create a conversation with the long title
        print("2. Creating conversation with long title...")
        conv_id = db.create_conversation(
            title=long_title,
            initial_prompt="Test prompt for long title conversation",
            agent_a_id="test_agent_a",
            agent_a_name="Test Agent A",
            agent_b_id="test_agent_b",
            agent_b_name="Test Agent B",
            tags=["test", "long-title-fix"]
        )

        print(f"\n✓ SUCCESS! Conversation created with ID: {conv_id}")

        # Verify we can load it back
        print("\n3. Verifying conversation can be loaded...")
        loaded = db.load_conversation(conv_id)

        if loaded:
            saved_title = loaded['conversation']['title']
            print(f"   ✓ Conversation loaded successfully")
            print(f"   Saved title length: {len(saved_title)} characters")
            print(f"   Saved title: {saved_title[:100]}...")
        else:
            print("   ✗ Failed to load conversation")
            return False

        # Clean up - delete test conversation
        print("\n4. Cleaning up test conversation...")
        if db.delete_conversation(conv_id):
            print("   ✓ Test conversation deleted")
        else:
            print("   ⚠️  Could not delete test conversation")

        db.close()

        print("\n" + "="*60)
        print("✓ TEST PASSED - Long title bug is FIXED!")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_long_title()
    sys.exit(0 if success else 1)
