#!/usr/bin/env python3
"""
Migration script to fix long conversation titles.

This script:
1. Finds all conversations with titles longer than 100 characters
2. Uses MetadataExtractor to generate concise titles
3. Updates the database with the new titles

Usage:
    python3 fix_long_titles.py [--dry-run]

Options:
    --dry-run    Show what would be changed without making changes
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager
from metadata_extractor import MetadataExtractor
from settings_manager import get_settings


def fix_long_titles(dry_run: bool = False):
    """
    Find and fix conversations with long titles.

    Args:
        dry_run: If True, show what would be changed without making changes
    """
    print("=" * 80)
    print("CONVERSATION TITLE FIX UTILITY")
    print("=" * 80)
    print()

    # Initialize database
    try:
        db = DatabaseManager()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1

    # Initialize MetadataExtractor
    try:
        # Try to get OpenAI API key from settings
        settings = get_settings()
        openai_key = settings.get_openai_api_key()

        if not openai_key:
            print("❌ OpenAI API key not configured")
            print("   Set it in settings or OPENAI_API_KEY environment variable")
            return 1

        metadata_extractor = MetadataExtractor(api_key=openai_key)
        print("✅ Initialized AI metadata extractor")
    except Exception as e:
        print(f"❌ Failed to initialize MetadataExtractor: {e}")
        return 1

    print()
    print("=" * 80)
    print("SCANNING FOR LONG TITLES...")
    print("=" * 80)
    print()

    # Find conversations with long titles (> 100 characters)
    try:
        with db.pg_conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, initial_prompt, created_at
                FROM conversations
                WHERE LENGTH(title) > 100
                ORDER BY created_at DESC
            """)
            long_title_conversations = cursor.fetchall()
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return 1

    if not long_title_conversations:
        print("✅ No conversations with long titles found!")
        return 0

    print(f"Found {len(long_title_conversations)} conversation(s) with long titles:\n")

    # Process each conversation
    updates_made = 0

    for conv in long_title_conversations:
        conv_id, old_title, initial_prompt, created_at = conv

        print("-" * 80)
        print(f"Conversation ID: {conv_id}")
        print(f"Created: {created_at}")
        print(f"Old title ({len(old_title)} chars):")
        print(f'  "{old_title[:100]}{"..." if len(old_title) > 100 else ""}"')

        # Generate new concise title
        try:
            new_title = metadata_extractor.generate_concise_title(old_title)
            print(f"\nNew title ({len(new_title)} chars):")
            print(f'  "{new_title}"')
        except Exception as e:
            print(f"⚠️  Error generating title: {e}")
            print("   Skipping this conversation...")
            continue

        # Update database (unless dry-run)
        if dry_run:
            print("\n🔍 DRY RUN - No changes made")
        else:
            try:
                with db.pg_conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE conversations
                        SET title = %s
                        WHERE id = %s
                    """, (new_title, conv_id))
                    db.pg_conn.commit()
                print("\n✅ Title updated successfully")
                updates_made += 1
            except Exception as e:
                print(f"\n❌ Error updating database: {e}")
                continue

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total conversations scanned: {len(long_title_conversations)}")

    if dry_run:
        print(f"Would update: {len(long_title_conversations)} conversation(s)")
        print("\nRun without --dry-run to apply changes")
    else:
        print(f"Successfully updated: {updates_made} conversation(s)")
        if updates_made < len(long_title_conversations):
            print(f"Failed/skipped: {len(long_title_conversations) - updates_made} conversation(s)")

    print()
    db.close()
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix long conversation titles in the database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )

    args = parser.parse_args()

    try:
        return fix_long_titles(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
