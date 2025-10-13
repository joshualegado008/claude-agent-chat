"""
Interactive menu system for managing conversations
"""

from typing import Optional, Tuple
from datetime import datetime
from db_manager import DatabaseManager
from conversation_manager_persistent import ConversationBrowser, PersistentConversationManager
from display_formatter import DisplayFormatter
from settings_manager import get_settings
from cost_calculator import CostCalculator
from metadata_extractor import MetadataExtractor


class ConversationMenu:
    """Interactive menu for conversation management."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.browser = ConversationBrowser(db_manager)

        # Initialize metadata extractor (optional - for automatic prompt/tag generation)
        try:
            # Try to get OpenAI API key from settings (works for both env vars and settings.json)
            settings = get_settings()
            openai_key = settings.get_openai_api_key()

            if openai_key:
                self.metadata_extractor = MetadataExtractor(api_key=openai_key)
                self.auto_metadata_enabled = True
            else:
                # No key available from either source
                raise ValueError("OpenAI API key not configured")

        except ValueError as e:
            # OpenAI key not available - fall back to manual input
            self.metadata_extractor = None
            self.auto_metadata_enabled = False
            DisplayFormatter.print_warning(f"⚠️  Automatic metadata extraction disabled: {e}")
            print("   You'll need to enter prompts and tags manually.")
            print("   Configure OpenAI key in Settings menu for automatic extraction.")

    def show_main_menu(self) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Show main menu and get user choice.

        Returns:
            Tuple of (action, conversation_id, continuation_prompt)
            - action: 'new', 'continue', 'search', 'quit'
            - conversation_id: UUID if continuing a conversation
            - continuation_prompt: Optional prompt for continuing
        """
        while True:
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " "*15 + "🤖 Agent Conversation Manager 🤖" + " "*11 + "║")
            print("╚" + "═"*58 + "╝\n")

            print("What would you like to do?\n")
            print("  1. 🆕 Start a new conversation")
            print("  2. 📁 Manage conversations (View/Continue/Delete)")
            print("  3. 🔍 Search past conversations")
            print("  4. 📋 List recent conversations")
            print("  5. ⚙️  Settings")
            print("  6. 🚪 Exit")

            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == '1':
                return ('new', None, None)

            elif choice == '2':
                return self._handle_manage_conversations()

            elif choice == '3':
                return self._handle_search()

            elif choice == '4':
                self._handle_list()
                continue  # Show menu again

            elif choice == '5':
                self._handle_settings()
                continue  # Show menu again

            elif choice == '6':
                return ('quit', None, None)

            else:
                print("\n❌ Invalid choice. Please enter 1-6.")

    def _handle_search(self) -> Tuple[str, Optional[str], Optional[str]]:
        """Handle searching conversations."""

        query = input("\n🔍 Enter search query: ").strip()

        if not query:
            return ('menu', None, None)

        print(f"\nSearching for: '{query}'...")
        results = self.browser.search(query, limit=10)

        if not results:
            print("\n❌ No matching conversations found.")
            input("Press Enter to return to menu...")
            return ('menu', None, None)

        print(f"\n✅ Found {len(results)} matching conversations:")
        print("="*80)

        # Display results with similarity scores
        for idx, result in enumerate(results, 1):
            score = result.get('similarity_score', 0)
            title = result.get('title', 'Untitled')[:40]
            preview = result.get('response_content', '')[:60]

            print(f"\n{idx}. {title} (Match: {score:.2%})")
            print(f"   Turn {result.get('turn_number', 0)} - {result.get('agent_name', 'N/A')}")
            print(f"   Preview: {preview}...")

        print("="*80)

        # Let user select one
        while True:
            choice = input("\nEnter number to open conversation (or 'b' to go back): ").strip()

            if choice.lower() == 'b':
                return ('menu', None, None)

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    conv_id = str(results[idx]['id'])

                    # Ask if they want to view or continue
                    print("\nWhat would you like to do?")
                    print("  1. View conversation")
                    print("  2. Continue conversation")
                    print("  3. Cancel")

                    action = input("\nChoice (1-3): ").strip()

                    if action == '1':
                        self._show_full_conversation(conv_id)
                        return ('menu', None, None)
                    elif action == '2':
                        return ('continue', conv_id, None)
                    else:
                        return ('menu', None, None)
                else:
                    print("❌ Invalid number.")
            except ValueError:
                print("❌ Please enter a valid number or 'b'.")

    def _handle_list(self):
        """Handle listing recent conversations."""

        conversations = self.browser.list_recent(limit=20)

        if not conversations:
            print("\n❌ No conversations found.")
        else:
            print(f"\n📋 Showing {len(conversations)} most recent conversations:")
            self.browser.display_conversation_list(conversations)

        input("\nPress Enter to continue...")

    def _continue_conversation(self, conv_id: str, conv: dict) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Handle continuing a specific conversation.

        Args:
            conv_id: The conversation ID
            conv: The conversation dictionary with metadata

        Returns:
            Tuple of (action, conversation_id, continuation_prompt)
        """
        # Ask how to continue
        print("\nHow would you like to continue?")
        print("  1. Continue with original topic")
        print("  2. Steer in a new direction")
        print("  3. Cancel")

        action = input("\nChoice (1-3): ").strip()

        if action == '1':
            return ('continue', conv_id, None)
        elif action == '2':
            new_prompt = input("\nEnter new direction/prompt: ").strip()
            if new_prompt:
                return ('continue', conv_id, new_prompt)
            else:
                print("\n❌ No prompt provided.")
                return ('menu', None, None)
        else:
            return ('menu', None, None)

    def _delete_conversation(self, conv_id: str, conv: dict):
        """
        Handle deleting a specific conversation.

        Args:
            conv_id: The conversation ID
            conv: The conversation dictionary with metadata
        """
        # Confirmation - require full "yes" for safety
        print("\n" + "="*80)
        print("⚠️  ⚠️  ⚠️  FINAL WARNING  ⚠️  ⚠️  ⚠️")
        print("="*80)
        print(f"\nYou are about to PERMANENTLY DELETE:")
        print(f"  Title: {conv.get('title', 'Untitled')}")
        print(f"  Turns: {conv.get('total_turns', 0)}")
        print(f"  Created: {conv.get('created_at', 'N/A')}")
        print("\nThis action CANNOT be undone!")
        print("All exchanges, metadata, and context will be permanently removed.")

        confirm = input("\nType 'yes' (all lowercase) to confirm deletion: ").strip()

        if confirm == 'yes':
            # Perform deletion
            DisplayFormatter.print_info("Deleting conversation...")

            if self.db.delete_conversation(conv_id):
                DisplayFormatter.print_success("✅ Conversation deleted successfully!")
            else:
                DisplayFormatter.print_error("❌ Failed to delete conversation. See error above.")

            input("\nPress Enter to continue...")
        else:
            print("\n❌ Deletion cancelled. (You must type 'yes' to confirm)")
            input("\nPress Enter to continue...")

    def _handle_manage_conversations(self) -> Tuple[str, Optional[str], Optional[str]]:
        """Handle managing conversations (view/continue/delete)."""

        while True:
            # Show recent conversations
            conversations = self.browser.list_recent(limit=20)

            if not conversations:
                print("\n❌ No conversations found.")
                input("Press Enter to return to menu...")
                return ('menu', None, None)

            print("\n" + "="*80)
            print("📁 Manage Conversations")
            print("="*80)

            self.browser.display_conversation_list(conversations)

            # Get user selection
            choice = input("\nEnter conversation number (or 'b' to go back): ").strip()

            if choice.lower() == 'b':
                return ('menu', None, None)

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(conversations):
                    conv = conversations[idx]
                    conv_id = str(conv['id'])

                    # Show conversation preview
                    self._show_conversation_preview(conv_id)

                    # Show action submenu
                    print("\n" + "="*60)
                    print("What would you like to do with this conversation?")
                    print("="*60)
                    print("  1. 👁️  View full conversation")
                    print("  2. ▶️  Continue conversation")
                    print("  3. 🗑️  Delete conversation")
                    print("  4. ◀️  Back to conversation list")

                    action = input("\nChoice (1-4): ").strip()

                    if action == '1':
                        # View full conversation
                        self._show_full_conversation(conv_id)
                        # After viewing, return to conversation list
                        continue

                    elif action == '2':
                        # Continue conversation
                        return self._continue_conversation(conv_id, conv)

                    elif action == '3':
                        # Delete conversation
                        self._delete_conversation(conv_id, conv)
                        # After deletion, refresh the list
                        continue

                    elif action == '4':
                        # Back to conversation list
                        continue

                    else:
                        print("\n❌ Invalid choice. Please enter 1-4.")
                        input("Press Enter to continue...")
                        continue

                else:
                    print("❌ Invalid number. Try again.")
                    input("Press Enter to continue...")

            except ValueError:
                print("❌ Please enter a valid number or 'b'.")
                input("Press Enter to continue...")

    def _handle_settings(self):
        """Handle settings configuration."""
        settings = get_settings()

        while True:
            print("\n" + "="*60)
            print("⚙️  Settings")
            print("="*60)

            print("\nWhat would you like to configure?\n")
            print("  1. 🔑 Configure API Keys")
            print("  2. 🤖 Select Models for Agents")
            print("  3. 🎨 Customize Display Colors")
            print("  4. 👁️  View Current Configuration")
            print("  5. 🧪 Test API Connections")
            print("  6. 🔧 Run Setup Wizard")
            print("  7. ◀️  Back to Main Menu")

            choice = input("\nEnter your choice (1-7): ").strip()

            if choice == '1':
                self._configure_api_keys(settings)
            elif choice == '2':
                self._configure_agent_models(settings)
            elif choice == '3':
                self._configure_colors(settings)
            elif choice == '4':
                settings.display_current_settings()
                input("\nPress Enter to continue...")
            elif choice == '5':
                self._test_api_connections(settings)
            elif choice == '6':
                settings.interactive_setup()
            elif choice == '7':
                break
            else:
                print("\n❌ Invalid choice. Please enter 1-7.")

    def _configure_api_keys(self, settings):
        """Configure API keys."""
        print("\n" + "="*60)
        print("🔑 API Key Configuration")
        print("="*60)

        print("\n1️⃣  Anthropic API Key (Required)")
        print("   Get your key from: https://console.anthropic.com/")
        current = settings.get_anthropic_api_key()
        if current:
            print(f"   Current: {settings.mask_key(current)}")

        update = input("\n   Update Anthropic key? (y/n): ").strip().lower()
        if update == 'y':
            new_key = input("   Enter new API key: ").strip()
            if new_key:
                print("   Testing key...")
                if settings.validate_anthropic_key(new_key):
                    settings.set_anthropic_api_key(new_key)
                    print("   ✅ Key validated and saved!")
                else:
                    print("   ❌ Key validation failed. Not saved.")

        print("\n2️⃣  OpenAI API Key (Optional - for semantic search)")
        print("   Get your key from: https://platform.openai.com/api-keys")
        current = settings.get_openai_api_key()
        if current:
            print(f"   Current: {settings.mask_key(current)}")

        update = input("\n   Update OpenAI key? (y/n): ").strip().lower()
        if update == 'y':
            new_key = input("   Enter new API key: ").strip()
            if new_key:
                print("   Testing key...")
                if settings.validate_openai_key(new_key):
                    settings.set_openai_api_key(new_key)
                    print("   ✅ Key validated and saved!")
                else:
                    print("   ❌ Key validation failed. Not saved.")

        input("\nPress Enter to continue...")

    def _configure_agent_models(self, settings):
        """Configure models for agents."""
        print("\n" + "="*60)
        print("🤖 Agent Model Configuration")
        print("="*60)

        available_models = CostCalculator.get_available_models()

        print("\nAvailable models:\n")
        for idx, model in enumerate(available_models, 1):
            print(f"  {idx}. {model['display_name']}")
            print(f"     Model: {model['name']}")
            print(f"     Pricing: ${model['input_price']:.2f}/${model['output_price']:.2f} per MTok (input/output)")
            print()

        # Configure Agent A
        print("Configure Agent A (Nova):")
        current_model = settings.get_agent_model('agent_a')
        current_display = CostCalculator._get_display_name(current_model)
        print(f"  Current: {current_display}")

        choice = input(f"\n  Select model (1-{len(available_models)}), or Enter to keep current: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                settings.set_agent_model('agent_a', available_models[idx]['name'])
                print(f"  ✅ Agent A set to {available_models[idx]['display_name']}")

        # Configure Agent B
        print("\nConfigure Agent B (Atlas):")
        current_model = settings.get_agent_model('agent_b')
        current_display = CostCalculator._get_display_name(current_model)
        print(f"  Current: {current_display}")

        choice = input(f"\n  Select model (1-{len(available_models)}), or Enter to keep current: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                settings.set_agent_model('agent_b', available_models[idx]['name'])
                print(f"  ✅ Agent B set to {available_models[idx]['display_name']}")

        input("\nPress Enter to continue...")

    def _test_api_connections(self, settings):
        """Test API connections."""
        print("\n" + "="*60)
        print("🧪 Testing API Connections")
        print("="*60)

        print("\nTesting Anthropic API...")
        if settings.validate_anthropic_key():
            print("✅ Anthropic API: Connected")
        else:
            print("❌ Anthropic API: Failed")

        print("\nTesting OpenAI API...")
        openai_key = settings.get_openai_api_key()
        if openai_key:
            if settings.validate_openai_key():
                print("✅ OpenAI API: Connected")
            else:
                print("❌ OpenAI API: Failed")
        else:
            print("⚠️  OpenAI API: Not configured (optional)")

        input("\nPress Enter to continue...")

    def _configure_colors(self, settings):
        """Configure display colors for thinking and agents."""
        try:
            from colorama import Fore, Style
            colors_available = True
        except ImportError:
            colors_available = False
            print("\n❌ Colorama not available. Colors cannot be customized.")
            input("\nPress Enter to continue...")
            return

        while True:
            print("\n" + "="*60)
            print("🎨 Display Color Configuration")
            print("="*60)

            # Show current colors
            print("\nCurrent Colors:")
            thinking_color = settings.get_thinking_color()
            agent_a_color = settings.get_agent_color('agent_a')
            agent_b_color = settings.get_agent_color('agent_b')

            # Display with actual colors
            thinking_color_obj = getattr(Fore, thinking_color, Fore.LIGHTYELLOW_EX)
            agent_a_color_obj = getattr(Fore, agent_a_color, Fore.CYAN)
            agent_b_color_obj = getattr(Fore, agent_b_color, Fore.YELLOW)

            print(f"  1. {thinking_color_obj}Thinking Text{Style.RESET_ALL} (Currently: {thinking_color})")
            print(f"  2. {agent_a_color_obj}Agent A - Nova{Style.RESET_ALL} (Currently: {agent_a_color})")
            print(f"  3. {agent_b_color_obj}Agent B - Atlas{Style.RESET_ALL} (Currently: {agent_b_color})")
            print("  4. ◀️  Back")

            choice = input("\nSelect element to customize (1-4): ").strip()

            if choice == '1':
                self._pick_color(settings, 'thinking', 'Thinking Text')
            elif choice == '2':
                self._pick_color(settings, 'agent_a', 'Agent A - Nova')
            elif choice == '3':
                self._pick_color(settings, 'agent_b', 'Agent B - Atlas')
            elif choice == '4':
                break
            else:
                print("\n❌ Invalid choice. Please enter 1-4.")

    def _pick_color(self, settings, target: str, display_name: str):
        """
        Show color picker and apply selection.

        Args:
            settings: SettingsManager instance
            target: 'thinking', 'agent_a', or 'agent_b'
            display_name: Human-readable name for display
        """
        try:
            from colorama import Fore, Style
        except ImportError:
            return

        print("\n" + "="*60)
        print(f"🎨 Select Color for {display_name}")
        print("="*60)

        # Get available colors
        colors = settings.get_available_colors()

        print("\nAvailable Colors (with preview):\n")

        # Display colors in two columns for better layout
        for idx, (color_code, color_display) in enumerate(colors, 1):
            color_obj = getattr(Fore, color_code, Fore.WHITE)
            # Show color preview
            preview = f"{color_obj}████ Sample Text{Style.RESET_ALL}"
            print(f"  {idx:2}. {preview:40} ({color_display})")

        print(f"\n  {len(colors) + 1}. Cancel")

        choice = input(f"\nSelect color (1-{len(colors) + 1}): ").strip()

        try:
            idx = int(choice) - 1
            if idx == len(colors):
                # Cancel
                return
            elif 0 <= idx < len(colors):
                color_code, color_display = colors[idx]

                # Preview the selection
                color_obj = getattr(Fore, color_code, Fore.WHITE)
                print(f"\n{color_obj}Preview: This is how {display_name} will look{Style.RESET_ALL}")

                confirm = input("\nApply this color? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Apply the color
                    try:
                        if target == 'thinking':
                            settings.set_thinking_color(color_code)
                        elif target == 'agent_a':
                            settings.set_agent_color('agent_a', color_code)
                        elif target == 'agent_b':
                            settings.set_agent_color('agent_b', color_code)

                        print(f"✅ Color for {display_name} set to {color_display}!")
                        print("\n💡 Note: Colors will take effect in new conversations.")
                    except ValueError as e:
                        print(f"❌ Error: {e}")
                else:
                    print("❌ Cancelled.")
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")

        input("\nPress Enter to continue...")

    def _show_conversation_preview(self, conversation_id: str):
        """Show a preview of a conversation."""
        data = self.db.load_conversation(conversation_id)

        if not data:
            print("\n❌ Conversation not found.")
            return

        conv = data['conversation']
        exchanges = data['exchanges']

        print("\n" + "="*80)
        print(f"📝 {conv['title']}")
        print("="*80)
        print(f"Initial prompt: {conv['initial_prompt']}")
        print(f"Agents: {conv['agent_a_name']} ↔ {conv['agent_b_name']}")
        print(f"Turns: {len(exchanges)}")
        print(f"Created: {conv['created_at']}")

        # Show last 3 exchanges
        if exchanges:
            print("\n📜 Recent exchanges:")
            for ex in exchanges[-3:]:
                print(f"\n  Turn {ex['turn_number']} - {ex['agent_name']}:")
                preview = ex['response_content'][:150]
                print(f"  {preview}...")

        print("="*80)

    def _show_full_conversation(self, conversation_id: str):
        """Show full conversation history."""
        manager = PersistentConversationManager(self.db)

        if not manager.load_conversation(conversation_id):
            print("\n❌ Failed to load conversation.")
            return

        print("\n" + manager.get_full_history())
        input("\nPress Enter to continue...")

    def get_new_conversation_details(self) -> Optional[dict]:
        """Get details for starting a new conversation."""

        print("\n" + "="*60)
        print("🆕 Starting a New Conversation")
        print("="*60)

        # Get title
        title = input("\nConversation title: ").strip()
        if not title:
            print("❌ Title is required.")
            return None

        # Use automatic metadata extraction if available
        if self.auto_metadata_enabled and self.metadata_extractor:
            print("\n" + "="*60)
            DisplayFormatter.print_info("✨ Analyzing conversation topic with AI...")
            print()

            try:
                # Generate initial prompt from title
                initial_prompt = self.metadata_extractor.generate_initial_prompt(title)
                print("💬 Generated Prompt:")
                print(f"   {initial_prompt}")
                print()

                # Extract tags
                tags = self.metadata_extractor.extract_tags_from_title(title)
                print(f"🏷️  Auto-generated Tags: {', '.join(tags)}")
                print()

                # Confirm with user
                confirm = input("Use this prompt and tags? [Y/n]: ").strip().lower()
                if confirm and confirm != 'y':
                    print("❌ Cancelled.")
                    return None

                return {
                    'title': title,
                    'initial_prompt': initial_prompt,
                    'tags': tags
                }

            except Exception as e:
                DisplayFormatter.print_warning(f"⚠️  AI generation failed: {e}")
                print("   Falling back to manual input...\n")
                # Fall through to manual input

        # Manual input (fallback or when auto-metadata is disabled)
        print("\nWhat should the agents discuss?")
        print("(Press Enter twice when done, or Ctrl+C to cancel)")

        lines = []
        try:
            while True:
                line = input()
                if not line and lines:
                    break
                lines.append(line)
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled.")
            return None

        initial_prompt = "\n".join(lines).strip()

        if not initial_prompt:
            print("❌ No prompt provided. Cancelled.")
            return None

        # Optional tags
        tags_input = input("\nAdd tags (comma-separated, optional): ").strip()
        tags = [t.strip() for t in tags_input.split(',')] if tags_input else []

        return {
            'title': title,
            'initial_prompt': initial_prompt,
            'tags': tags
        }
