"""
Contextual Coordinator - Main entry point for AI-powered conversation system
Features streamlined input, rich metadata extraction, and interactive dashboard
"""

import os
import sys
from colorama import Style
from display_formatter import DisplayFormatter
from db_manager import DatabaseManager
from interactive_coordinator import InteractiveCoordinator


def check_prerequisites():
    """Check that all required API keys and services are available."""
    missing = []

    # Check API keys
    if not os.environ.get('ANTHROPIC_API_KEY'):
        missing.append("ANTHROPIC_API_KEY - Get from: https://console.anthropic.com/")

    if not os.environ.get('OPENAI_API_KEY'):
        missing.append("OPENAI_API_KEY - Get from: https://platform.openai.com/api-keys")

    if missing:
        print("\n❌ Missing required API keys:\n")
        for item in missing:
            print(f"   • {item}")
        print("\nPlease set these environment variables:")
        print("   export ANTHROPIC_API_KEY='sk-ant-...'")
        print("   export OPENAI_API_KEY='sk-...'")
        print()
        return False

    return True


def main():
    """Main entry point."""

    # Print header
    DisplayFormatter.print_header()
    print("              with AI-Powered Contextual Intelligence")
    print()

    # Check prerequisites
    if not check_prerequisites():
        return 1

    # Connect to databases
    try:
        DisplayFormatter.print_info("Connecting to databases...")
        db = DatabaseManager()
        DisplayFormatter.print_success("Connected to PostgreSQL and Qdrant")
        DisplayFormatter.print_success("AI metadata extraction enabled (GPT-4o-mini)")
    except Exception as e:
        DisplayFormatter.print_error(f"Failed to connect to databases: {e}")
        print("\n📝 Make sure Docker services are running:")
        print("   docker-compose up -d")
        return 1

    # Configuration
    config = {
        'agent_a': {'id': 'agent_a', 'name': 'Nova'},
        'agent_b': {'id': 'agent_b', 'name': 'Atlas'},
        'max_turns': 20,
        'show_thinking': True,
        'show_metadata_updates': False,  # Set to True for live metadata updates
    }

    # Initialize interactive coordinator
    coordinator = InteractiveCoordinator(db)

    # Main loop
    while True:
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " "*15 + "🤖 Agent Conversation Manager 🤖" + " "*11 + "║")
        print("╚" + "═"*58 + "╝\n")

        print("What would you like to do?\n")
        print(f"  {DisplayFormatter.AGENT_COLORS['Nova']}1.{Style.RESET_ALL} 🆕 Start a new conversation")
        print(f"  {DisplayFormatter.AGENT_COLORS['Atlas']}2.{Style.RESET_ALL} ▶️  Continue a previous conversation")
        print(f"  3. 🔍 Search past conversations")
        print(f"  4. 📋 List recent conversations")
        print(f"  5. 📊 View conversation analytics")
        print(f"  6. ⚙️  Settings")
        print(f"  7. 🚪 Exit")
        print()

        choice = input("Enter your choice (1-7): ").strip()

        if choice == '1':
            # Start new conversation - streamlined!
            print("\n" + "="*60)
            print("🆕 Starting a New Conversation")
            print("="*60)
            print()

            title = input("Conversation title: ").strip()

            if not title:
                print("\n❌ Title is required.")
                continue

            # Run streamlined conversation start
            coordinator.start_new_conversation_streamlined(title, config)

            input("\n\nPress Enter to return to menu...")

        elif choice == '2':
            # Continue previous conversation
            print("\n🔨 Feature: Continue previous conversation")
            print("   (Use existing coordinator_with_memory.py for now)")
            input("\nPress Enter to continue...")

        elif choice == '3':
            # Search conversations
            print("\n🔨 Feature: Search conversations")
            print("   (Use existing coordinator_with_memory.py for now)")
            input("\nPress Enter to continue...")

        elif choice == '4':
            # List recent
            _list_recent_conversations(db)
            input("\nPress Enter to continue...")

        elif choice == '5':
            # Analytics
            _show_analytics(db)
            input("\nPress Enter to continue...")

        elif choice == '6':
            # Settings
            _show_settings(config)
            input("\nPress Enter to continue...")

        elif choice == '7':
            print("\n👋 Goodbye!")
            db.close()
            return 0

        else:
            print("\n❌ Invalid choice. Please enter 1-7.")


def _list_recent_conversations(db: DatabaseManager):
    """List recent conversations with metadata."""
    from conversation_manager_persistent import ConversationBrowser

    browser = ConversationBrowser(db)
    conversations = browser.list_recent(limit=10)

    if not conversations:
        print("\n❌ No conversations found.")
        return

    print("\n" + "="*80)
    print(f"📋 Recent Conversations (Last 10)")
    print("="*80)

    for idx, conv in enumerate(conversations, 1):
        title = conv.get('title', 'Untitled')
        turns = conv.get('total_turns', 0)
        created = conv.get('created_at', 'N/A')

        if hasattr(created, 'strftime'):
            created = created.strftime('%Y-%m-%d %H:%M')

        print(f"\n{idx}. {title}")
        print(f"   Turns: {turns} • Created: {created}")
        print(f"   ID: {conv.get('id', 'N/A')}")


def _show_analytics(db: DatabaseManager):
    """Show conversation analytics from metadata."""
    print("\n" + "="*80)
    print("📊 Conversation Analytics")
    print("="*80)

    try:
        # Most discussed topics
        with db.pg_conn.cursor() as cursor:
            cursor.execute("""
                SELECT topic, frequency
                FROM topic_frequency
                ORDER BY frequency DESC
                LIMIT 10
            """)

            topics = cursor.fetchall()

            if topics:
                print("\n🎓 Most Discussed Topics:")
                print("─"*60)
                for topic, freq in topics:
                    bar = "█" * min(freq, 20)
                    print(f"  {topic:30} {bar} ({freq})")

            # Entity statistics
            cursor.execute("""
                SELECT entity_type, COUNT(DISTINCT entity_name) as unique_count
                FROM entity_analytics
                GROUP BY entity_type
            """)

            entities = cursor.fetchall()

            if entities:
                print("\n🔍 Named Entity Statistics:")
                print("─"*60)
                for entity_type, count in entities:
                    print(f"  {entity_type:20} {count} unique")

            # Conversation stages
            cursor.execute("""
                SELECT conversation_stage, COUNT(*) as count
                FROM conversation_metadata
                GROUP BY conversation_stage
                ORDER BY count DESC
            """)

            stages = cursor.fetchall()

            if stages:
                print("\n🎯 Conversation Stages Distribution:")
                print("─"*60)
                for stage, count in stages:
                    print(f"  {stage:20} {count}")

    except Exception as e:
        print(f"\n⚠️  Analytics unavailable: {e}")


def _show_settings(config: dict):
    """Show and modify settings."""
    print("\n" + "="*60)
    print("⚙️  Settings")
    print("="*60)

    print(f"\n1. Agent A: {config['agent_a']['name']} ({config['agent_a']['id']})")
    print(f"2. Agent B: {config['agent_b']['name']} ({config['agent_b']['id']})")
    print(f"3. Max Turns: {config['max_turns']}")
    print(f"4. Show Thinking: {config['show_thinking']}")
    print(f"5. Show Metadata Updates: {config['show_metadata_updates']}")
    print("\n(Settings modification coming soon)")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
