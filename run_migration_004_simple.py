#!/usr/bin/env python3
"""
Run database migration 004: Support multiple agents (simplified)
"""

import psycopg2
import sys

def run_migration():
    """Run migration 004 to add agents JSONB column."""

    print("="*60)
    print("Migration 004: Support multiple agents (simplified)")
    print("="*60)

    try:
        # Connect to database
        print("\n1. Connecting to database...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="agent_conversations",
            user="agent_user",
            password="agent_pass_local"
        )
        conn.set_session(autocommit=False)
        cursor = conn.cursor()

        # Check if agents column already exists
        print("\n2. Checking if agents column exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'conversations'
                AND column_name = 'agents'
            )
        """)
        column_exists = cursor.fetchone()[0]

        if column_exists:
            print("   ✓ Migration already applied - agents column exists")
            cursor.close()
            conn.close()
            return True

        # Add agents column
        print("\n3. Adding agents JSONB column...")
        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN agents JSONB DEFAULT NULL
        """)
        print("   ✓ Column added")

        # Add index
        print("\n4. Adding GIN index on agents column...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_agents
            ON conversations USING GIN(agents)
        """)
        print("   ✓ Index created")

        # Migrate existing data
        print("\n5. Migrating existing conversation data...")
        cursor.execute("""
            UPDATE conversations
            SET agents = jsonb_build_array(
                jsonb_build_object(
                    'id', agent_a_id,
                    'name', agent_a_name,
                    'qualification', NULL
                ),
                jsonb_build_object(
                    'id', agent_b_id,
                    'name', agent_b_name,
                    'qualification', NULL
                )
            )
            WHERE agents IS NULL
        """)
        rows_updated = cursor.rowcount
        print(f"   ✓ Migrated {rows_updated} existing conversations")

        # Commit changes
        print("\n6. Committing changes...")
        conn.commit()
        print("   ✓ Changes committed")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("✓ Migration 004 completed successfully!")
        print("="*60)
        print("\nYou can now create conversations with 3+ agents.")
        return True

    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        if conn:
            conn.rollback()
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. No active conversations are being created")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
