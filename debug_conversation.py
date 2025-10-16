#!/usr/bin/env python3
"""Debug script to check conversation data in database."""

import sys
from db_manager import DatabaseManager

# The conversation ID to check
CONV_ID = '02a47e3c-503e-4df0-ab6c-df23badc2050'

def main():
    print("=" * 80)
    print("CONVERSATION DATABASE DEBUG")
    print("=" * 80)
    print()

    # Initialize database
    try:
        db = DatabaseManager()
        print("✅ Connected to database\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1

    # Check conversation record
    print(f"Checking conversation: {CONV_ID}\n")
    print("-" * 80)

    try:
        with db.pg_conn.cursor() as cursor:
            # Get conversation metadata
            cursor.execute("""
                SELECT id, title, total_turns, total_tokens, status, created_at, updated_at
                FROM conversations
                WHERE id = %s
            """, (CONV_ID,))

            conv = cursor.fetchone()

            if not conv:
                print(f"❌ Conversation not found in database!")
                return 1

            conv_id, title, total_turns, total_tokens, status, created_at, updated_at = conv

            print("CONVERSATION RECORD:")
            print(f"  ID: {conv_id}")
            print(f"  Title: {title[:80]}...")
            print(f"  Total Turns (stored): {total_turns}")
            print(f"  Total Tokens (stored): {total_tokens}")
            print(f"  Status: {status}")
            print(f"  Created: {created_at}")
            print(f"  Updated: {updated_at}")
            print()

            # Count actual exchanges
            cursor.execute("""
                SELECT COUNT(*) FROM exchanges WHERE conversation_id = %s
            """, (CONV_ID,))

            actual_count = cursor.fetchone()[0]
            print(f"ACTUAL EXCHANGES IN DATABASE: {actual_count}")
            print()

            # Show discrepancy if any
            if actual_count != total_turns:
                print("⚠️  MISMATCH DETECTED!")
                print(f"  Stored total_turns: {total_turns}")
                print(f"  Actual exchanges: {actual_count}")
                print(f"  Discrepancy: {actual_count - total_turns}")
                print()

            # Show first and last exchanges
            cursor.execute("""
                SELECT turn_number, agent_name, created_at
                FROM exchanges
                WHERE conversation_id = %s
                ORDER BY turn_number
                LIMIT 5
            """, (CONV_ID,))

            first_exchanges = cursor.fetchall()
            print("FIRST 5 EXCHANGES:")
            for turn, agent, created in first_exchanges:
                print(f"  Turn {turn}: {agent} at {created}")
            print()

            cursor.execute("""
                SELECT turn_number, agent_name, created_at
                FROM exchanges
                WHERE conversation_id = %s
                ORDER BY turn_number DESC
                LIMIT 5
            """, (CONV_ID,))

            last_exchanges = cursor.fetchall()
            print("LAST 5 EXCHANGES:")
            for turn, agent, created in reversed(list(last_exchanges)):
                print(f"  Turn {turn}: {agent} at {created}")
            print()

    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 80)
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
