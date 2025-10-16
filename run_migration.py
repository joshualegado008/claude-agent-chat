#!/usr/bin/env python3
"""
Run database migration 003: Increase title length

This script applies the migration to increase the conversation title column
from VARCHAR(255) to TEXT.
"""

import psycopg2
import sys

def run_migration():
    """Run the migration to increase title column size."""

    print("="*60)
    print("Migration 003: Increase conversation title length")
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

        # Create cursor
        cursor = conn.cursor()

        # Check current column type
        print("\n2. Checking current column type...")
        cursor.execute("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'conversations'
            AND column_name = 'title'
        """)
        current_type = cursor.fetchone()
        print(f"   Current type: {current_type[0]}", end="")
        if current_type[1]:
            print(f"({current_type[1]})")
        else:
            print()

        # Check if migration is needed
        if current_type[0] == 'text':
            print("\n✓ Migration already applied - title column is already TEXT")
            cursor.close()
            conn.close()
            return True

        # Apply migration
        print("\n3. Applying migration...")
        cursor.execute("""
            ALTER TABLE conversations
            ALTER COLUMN title TYPE TEXT
        """)

        # Commit the change
        conn.commit()
        print("   ✓ ALTER TABLE executed successfully")

        # Verify the change
        print("\n4. Verifying migration...")
        cursor.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'conversations'
            AND column_name = 'title'
        """)
        new_type = cursor.fetchone()

        if new_type[0] == 'text':
            print(f"   ✓ Verified: title column is now {new_type[0].upper()}")
        else:
            print(f"   ✗ Error: title column is still {new_type[0]}")
            cursor.close()
            conn.close()
            return False

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print("✓ Migration completed successfully!")
        print("="*60)
        print("\nYou can now create conversations with titles longer than 255 characters.")
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
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
