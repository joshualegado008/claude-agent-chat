#!/usr/bin/env python3
"""
Cleanup Duplicate Agent Files

This script removes duplicate agent files created before the name uniqueness
fix was implemented in v0.4.1. It keeps the most recent file for each unique
agent name and deletes older duplicates.

Usage:
    python3 cleanup_duplicate_agents.py --dry-run  # Preview what will be deleted
    python3 cleanup_duplicate_agents.py            # Actually delete duplicates
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import argparse


def extract_agent_name(md_file: Path) -> str:
    """Extract agent name from markdown file's first header line."""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('# '):
                    # Extract name (e.g., "# Dr. Jane Smith - Expert in X")
                    name = line[2:].split(' - ')[0].strip()
                    return name
    except Exception as e:
        print(f"   ⚠️  Error reading {md_file.name}: {e}")
    return None


def find_duplicates(agents_dir: Path):
    """Find all duplicate agent files grouped by name."""
    name_to_files = defaultdict(list)

    for md_file in agents_dir.glob('*.md'):
        name = extract_agent_name(md_file)
        if name:
            name_to_files[name].append({
                'md_file': md_file,
                'agent_id': md_file.stem,
                'mtime': md_file.stat().st_mtime
            })

    return name_to_files


def identify_files_to_delete(name_to_files: dict, data_dir: Path):
    """Identify which files should be deleted (keep most recent, delete older)."""
    files_to_delete = []

    for name, files in name_to_files.items():
        if len(files) > 1:
            # Sort by modification time (most recent first)
            files.sort(key=lambda x: x['mtime'], reverse=True)

            # Keep the first (most recent), delete the rest
            keep_file = files[0]
            delete_files = files[1:]

            for file_info in delete_files:
                md_path = file_info['md_file']
                json_path = data_dir / f"{file_info['agent_id']}.json"

                files_to_delete.append({
                    'name': name,
                    'md_path': md_path,
                    'json_path': json_path if json_path.exists() else None,
                    'mtime': datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M')
                })

    return files_to_delete


def print_report(name_to_files: dict, files_to_delete: list):
    """Print a detailed report of what will be cleaned up."""
    print("\n" + "=" * 80)
    print("DUPLICATE AGENT CLEANUP REPORT")
    print("=" * 80)

    # Summary
    total_files = sum(len(files) for files in name_to_files.values())
    unique_names = len(name_to_files)
    duplicates = sum(1 for files in name_to_files.values() if len(files) > 1)

    print(f"\n📊 Summary:")
    print(f"   Total agent files: {total_files}")
    print(f"   Unique agent names: {unique_names}")
    print(f"   Agent names with duplicates: {duplicates}")
    print(f"   Files to delete: {len(files_to_delete)}")
    print(f"   Files to keep: {unique_names}")

    # Detailed list
    print(f"\n📋 Duplicates to be deleted:")
    print("-" * 80)

    current_name = None
    for file_info in sorted(files_to_delete, key=lambda x: x['name']):
        if file_info['name'] != current_name:
            current_name = file_info['name']
            count = sum(1 for f in files_to_delete if f['name'] == current_name)
            print(f"\n{current_name} ({count} duplicates):")

        json_status = "✓ JSON" if file_info['json_path'] else "✗ no JSON"
        print(f"   🗑️  {file_info['md_path'].name} ({file_info['mtime']}) {json_status}")

    print("\n" + "=" * 80)


def delete_files(files_to_delete: list, dry_run: bool = True):
    """Delete the duplicate files."""
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be deleted")
        print("    Run without --dry-run to actually delete files")
        return

    print("\n🗑️  Deleting duplicate files...")

    deleted_md = 0
    deleted_json = 0
    errors = []

    for file_info in files_to_delete:
        # Delete .md file
        try:
            file_info['md_path'].unlink()
            deleted_md += 1
            print(f"   ✓ Deleted: {file_info['md_path'].name}")
        except Exception as e:
            error_msg = f"Failed to delete {file_info['md_path'].name}: {e}"
            errors.append(error_msg)
            print(f"   ❌ {error_msg}")

        # Delete .json file if it exists
        if file_info['json_path']:
            try:
                file_info['json_path'].unlink()
                deleted_json += 1
                print(f"   ✓ Deleted: {file_info['json_path'].name}")
            except Exception as e:
                error_msg = f"Failed to delete {file_info['json_path'].name}: {e}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")

    print("\n" + "=" * 80)
    print(f"✅ Cleanup complete!")
    print(f"   Deleted {deleted_md} .md files")
    print(f"   Deleted {deleted_json} .json files")

    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for error in errors:
            print(f"   - {error}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Cleanup duplicate agent files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cleanup_duplicate_agents.py --dry-run   # Preview changes
  python3 cleanup_duplicate_agents.py             # Execute cleanup
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without deleting files'
    )

    args = parser.parse_args()

    # Paths
    agents_dir = Path('.claude/agents/dynamic')
    data_dir = Path('data/agents')

    # Validate directories exist
    if not agents_dir.exists():
        print(f"❌ Error: Directory not found: {agents_dir}")
        sys.exit(1)

    if not data_dir.exists():
        print(f"⚠️  Warning: Directory not found: {data_dir}")

    # Find duplicates
    print("🔍 Scanning for duplicate agents...")
    name_to_files = find_duplicates(agents_dir)
    files_to_delete = identify_files_to_delete(name_to_files, data_dir)

    # Print report
    print_report(name_to_files, files_to_delete)

    # Delete files
    if files_to_delete:
        delete_files(files_to_delete, dry_run=args.dry_run)
    else:
        print("\n✅ No duplicate files found!")


if __name__ == '__main__':
    main()
