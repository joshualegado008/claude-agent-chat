#!/usr/bin/env python3
"""
Run database migration 004: Support multiple agents

This script applies the migration to add agents JSONB column
for supporting 3+ agents in conversations.
"""

import psycopg2
import sys

def run_migration():
    """Run migration 004 to add agents JSONB column."""

    print("="*60)
    print("Migration 004: Support multiple agents")
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

        # Read migration SQL file
        print("\n2. Reading migration file...")
        with open('migrations/004_support_multi_agents.sql', 'r') as f:
            migration_sql = f.read()

        # Execute migration
        print("\n3. Executing migration...")
        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()

        print("\n✓ Migration executed successfully!")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("✓ Migration 004 completed!")
        print("="*60)
        print("\nYou can now create conversations with 3+ agents.")
        return True

    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running (docker-compose up -d)")
        print("  2. Database credentials are correct")
        print("  3. No other process has the table locked")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
