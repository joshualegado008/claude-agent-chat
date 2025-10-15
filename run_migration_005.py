#!/usr/bin/env python3
"""
Run database migration 005: Add conversation summaries support

This migration adds the conversation_summaries table for storing
AI-generated Post-Conversation Intelligence Reports.
"""

import psycopg2
import sys


def run_migration():
    """Run migration 005 to add conversation summaries table."""

    print("="*60)
    print("Migration 005: Add conversation summaries support")
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

        # Check if table already exists
        print("\n2. Checking if ai_summaries table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'ai_summaries'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if table_exists:
            print("   ✓ Migration already applied - ai_summaries table exists")
            cursor.close()
            conn.close()
            return True

        # Read and execute migration file
        print("\n3. Creating conversation_summaries table...")
        with open('migrations/005_add_conversation_summaries.sql', 'r') as f:
            migration_sql = f.read()

        cursor.execute(migration_sql)
        print("   ✓ Table created successfully")

        # Verify table was created
        print("\n4. Verifying table structure...")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'ai_summaries'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()

        print("   Columns created:")
        for col_name, col_type in columns:
            print(f"     - {col_name}: {col_type}")

        # Commit changes
        print("\n5. Committing changes...")
        conn.commit()
        print("   ✓ Changes committed")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("✓ Migration 005 completed successfully!")
        print("="*60)
        print("\nConversation summaries are now enabled.")
        print("Summaries will be generated automatically for new conversations.")
        return True

    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        if conn:
            conn.rollback()
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database credentials are correct")
        print("  3. Migration file exists: migrations/005_add_conversation_summaries.sql")
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
