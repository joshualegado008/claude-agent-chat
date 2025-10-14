"""
Multi-Agent Conversation Coordinator with Persistent Memory
Supports: New conversations, continuing previous ones, and semantic search
"""

import os
import sys
import signal
import json
from typing import Optional, Dict
from datetime import datetime
from agent_runner import AgentPool
from display_formatter import DisplayFormatter
from db_manager import DatabaseManager
from conversation_manager_persistent import PersistentConversationManager
from menu import ConversationMenu
from settings_manager import get_settings
from cost_calculator import CostCalculator

# Optional imports for rich contextual intelligence
try:
    from metadata_extractor import MetadataExtractor
    from terminal_dashboard import TerminalDashboard
    RICH_CONTEXT_AVAILABLE = True
except ImportError:
    RICH_CONTEXT_AVAILABLE = False

# Phase 1E: Dynamic multi-agent system
from src.agent_coordinator import AgentCoordinator
from src.data_models import AgentProfile
from pathlib import Path
import asyncio


class ConversationInterruptHandler:
    """Handles Ctrl-C interrupts during conversations with interactive menu."""

    def __init__(
        self,
        metadata_extractor: Optional['MetadataExtractor'] = None,
        dashboard: Optional['TerminalDashboard'] = None
    ):
        self.interrupt_requested = False
        self.original_sigint_handler = None
        self.metadata_extractor = metadata_extractor
        self.dashboard = dashboard
        self.current_metadata: Optional[Dict] = None

    def install_handler(self):
        """Install the SIGINT handler."""
        self.original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)

    def restore_handler(self):
        """Restore the original SIGINT handler."""
        if self.original_sigint_handler:
            signal.signal(signal.SIGINT, self.original_sigint_handler)

    def _signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl-C) gracefully."""
        self.interrupt_requested = True

    def check_interrupt(self) -> bool:
        """Check if interrupt was requested and reset the flag."""
        if self.interrupt_requested:
            self.interrupt_requested = False
            return True
        return False

    def extract_metadata_if_available(
        self,
        conv_manager: PersistentConversationManager,
        current_turn: int
    ):
        """Extract metadata if MetadataExtractor is available."""
        if not self.metadata_extractor:
            return

        try:
            recent_exchanges = conv_manager.exchanges[-10:] if conv_manager.exchanges else []
            self.current_metadata = self.metadata_extractor.analyze_conversation_snapshot(
                recent_exchanges=recent_exchanges,
                title=conv_manager.metadata.get('title', 'Untitled'),
                total_turns=current_turn
            )
        except Exception as e:
            # Silently fail - metadata extraction is optional
            pass

    def show_interrupt_menu(
        self,
        conv_manager: PersistentConversationManager,
        current_turn: int,
        total_tokens: int,
        total_cost: float
    ) -> tuple[str, Optional[str]]:
        """
        Show interrupt menu and handle user choice.

        Returns:
            Tuple of (action, injected_content) where:
            - action: 'resume', 'stop', or 'inject'
            - injected_content: The injected text if action is 'inject', None otherwise
        """
        # Temporarily restore default Ctrl-C behavior for menu
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        try:
            print("\n")
            print("=" * 60)
            print("⏸️  CONVERSATION PAUSED")
            print("=" * 60)
            print("\nWhat would you like to do?\n")
            print("  1. 📊 View Conversation Context")
            print("  2. 💬 Inject content into conversation")
            print("  3. ▶️  Resume Conversation")
            print("  4. ⏹️  Stop Conversation")
            print()

            choice = input("Enter your choice (1-4): ").strip()

            if choice == '1':
                # View context - extract fresh metadata if available
                self.extract_metadata_if_available(conv_manager, current_turn)
                self._show_conversation_context(conv_manager, current_turn, total_tokens, total_cost)
                input("\nPress Enter to continue...")
                return ('resume', None)

            elif choice == '2':
                # Inject content
                injected_content = self.handle_user_injection()
                if injected_content:
                    return ('inject', injected_content)
                else:
                    # Injection was cancelled, show menu again
                    return self.show_interrupt_menu(conv_manager, current_turn, total_tokens, total_cost)

            elif choice == '3' or not choice:
                # Resume
                print("\n▶️  Resuming conversation...")
                return ('resume', None)

            elif choice == '4':
                # Stop
                confirm = input("\n⚠️  Stop conversation and save progress? [y/N]: ").strip().lower()
                if confirm == 'y':
                    return ('stop', None)
                return ('resume', None)

            else:
                print("\n❌ Invalid choice. Resuming conversation...")
                return ('resume', None)

        finally:
            # Restore our custom SIGINT handler
            signal.signal(signal.SIGINT, self._signal_handler)

    def _show_conversation_context(
        self,
        conv_manager: PersistentConversationManager,
        current_turn: int,
        total_tokens: int,
        total_cost: float
    ):
        """Display conversation context - rich dashboard if available, else simple view."""

        # Try to show rich dashboard if metadata is available
        if self.current_metadata and self.dashboard:
            try:
                self.dashboard.display_full_dashboard(
                    metadata=self.current_metadata,
                    conversation_title=conv_manager.metadata.get('title', 'Untitled'),
                    total_turns=current_turn,
                    total_tokens=total_tokens,
                    total_cost=total_cost
                )
                return  # Successfully showed rich dashboard
            except Exception as e:
                # Fall through to simple view
                print(f"\n⚠️  Rich dashboard unavailable: {e}")

        # Fall back to simple text view
        print("\n" + "=" * 80)
        print("📊 CONVERSATION CONTEXT")
        print("=" * 80)

        # Conversation info
        print(f"\n🎯 Title: {conv_manager.metadata.get('title', 'Untitled')}")
        print(f"📈 Progress: Turn {current_turn}")
        print(f"💰 Tokens Used: {total_tokens:,}")
        if total_cost > 0:
            cost_str = CostCalculator.format_cost(total_cost)
            print(f"💵 Cost So Far: {cost_str}")

        # Recent exchanges
        recent_exchanges = conv_manager.exchanges[-5:] if conv_manager.exchanges else []

        if recent_exchanges:
            print(f"\n📜 Recent Exchanges (last {len(recent_exchanges)}):")
            print("-" * 80)

            for ex in recent_exchanges:
                turn_num = ex.get('turn_number', 0)
                agent = ex.get('agent_name', 'Unknown')
                content = ex.get('response_content', '')

                # Show first 200 chars of response
                preview = content[:200] + "..." if len(content) > 200 else content

                print(f"\nTurn {turn_num} - {agent}:")
                print(f"  {preview}")

        print("\n" + "=" * 80)

        # Show hint if rich context is not available
        if not self.current_metadata:
            print("\n💡 Tip: Configure OpenAI API key in Settings for AI-powered context analysis")

    def handle_user_injection(self) -> Optional[str]:
        """
        Handle user content injection - prompt for free-form text input.

        Returns:
            The injected content, or None if cancelled
        """
        print("\n" + "="*60)
        print("💬 INJECT CONTENT INTO CONVERSATION")
        print("="*60)
        print("\nEnter content to inject (text, question, URL, etc.)")
        print("This can be:")
        print("  • A question or statement")
        print("  • A new theory or idea to explore")
        print("  • A URL for agents to research (they have fetch_url tool)")
        print("  • Any other material to incorporate")
        print("\nPress Enter twice when done, or Ctrl-C to cancel\n")

        lines = []
        try:
            while True:
                line = input()
                if not line and lines:
                    # Empty line and we have content - done
                    break
                lines.append(line)
        except KeyboardInterrupt:
            print("\n\n❌ Injection cancelled.")
            return None

        content = "\n".join(lines).strip()

        if not content:
            print("\n❌ No content provided. Injection cancelled.")
            return None

        # Check for URLs
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, content)

        # Show preview
        print("\n" + "-"*60)
        print("PREVIEW:")
        print("-"*60)
        preview = content[:200] + "..." if len(content) > 200 else content
        print(preview)

        if urls:
            print(f"\n💡 Detected {len(urls)} URL(s). Agents can use their fetch_url tool to read:")
            for url in urls[:3]:  # Show first 3 URLs
                print(f"   • {url}")

        print("-"*60)

        # Confirm
        confirm = input("\n✓ Inject this content? [Y/n]: ").strip().lower()

        if confirm and confirm != 'y':
            print("\n❌ Injection cancelled.")
            return None

        return content


def main():
    """Main coordinator with database-backed memory."""

    # Print header
    DisplayFormatter.print_header()

    # Load full config from file
    import yaml
    from pathlib import Path
    config_path = Path('config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            full_config = yaml.safe_load(f)
    else:
        full_config = {
            'agents': {},
            'conversation': {},
            'display': {}
        }

    # Configuration
    config = {
        'agent_a': {'id': 'agent_a', 'name': 'Nova'},
        'agent_b': {'id': 'agent_b', 'name': 'Atlas'},
        'max_turns': full_config.get('conversation', {}).get('max_turns', 20),
        'show_thinking': full_config.get('conversation', {}).get('show_thinking', True),
        'stats_mode': full_config.get('display', {}).get('stats_mode', 'simple'),
        'full_config': full_config  # Store full config for access
    }

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        DisplayFormatter.print_error("ANTHROPIC_API_KEY environment variable not set!")
        print("\n📝 Please follow these steps:")
        print("   1. Get API key from: https://console.anthropic.com/")
        print("   2. Set environment variable:")
        print("      export ANTHROPIC_API_KEY='sk-ant-...'")
        return 1

    # Initialize database connection
    try:
        DisplayFormatter.print_info("Connecting to databases...")
        db = DatabaseManager()
        DisplayFormatter.print_success("Connected to PostgreSQL and Qdrant")
    except Exception as e:
        DisplayFormatter.print_error(f"Failed to connect to databases: {e}")
        print("\n📝 Make sure Docker services are running:")
        print("   docker-compose up -d")
        print("\nSee SETUP_DATABASE.md for detailed instructions.")
        return 1

    # Initialize dynamic agent management system
    try:
        DisplayFormatter.print_info("Initializing agent management...")
        agent_coordinator = AgentCoordinator(verbose=False)  # Set verbose=False to reduce startup noise
        DisplayFormatter.print_success("✨ Dynamic agent management enabled")
    except Exception as e:
        DisplayFormatter.print_error(f"Failed to initialize agent coordinator: {e}")
        print("\n⚠️  Falling back to static agents (Nova & Atlas)")
        agent_coordinator = None

    # Show menu and get user choice
    menu = ConversationMenu(db)

    while True:
        action, conversation_id, continuation_prompt = menu.show_main_menu()

        if action == 'quit':
            DisplayFormatter.print_info("Goodbye!")
            db.close()
            return 0

        elif action == 'menu':
            continue  # Show menu again

        elif action == 'new':
            # Start new conversation
            details = menu.get_new_conversation_details()
            if not details:
                continue

            run_conversation(
                db, config, agent_coordinator,
                conversation_mode='new',
                title=details['title'],
                initial_prompt=details['initial_prompt'],
                tags=details['tags']
            )

        elif action == 'continue':
            # Continue existing conversation
            run_conversation(
                db, config, agent_coordinator,
                conversation_mode='continue',
                conversation_id=conversation_id,
                continuation_prompt=continuation_prompt
            )


def run_conversation(
    db: DatabaseManager,
    config: dict,
    agent_coordinator: Optional[AgentCoordinator],
    conversation_mode: str = 'new',
    conversation_id: str = None,
    title: str = None,
    initial_prompt: str = None,
    continuation_prompt: str = None,
    tags: list = None
):
    """
    Run a conversation (new or continued).

    Args:
        db: Database manager
        config: Configuration dict
        agent_coordinator: Dynamic agent coordinator (None = use static agents)
        conversation_mode: 'new' or 'continue'
        conversation_id: UUID for continuing
        title: Title for new conversation
        initial_prompt: Initial prompt for new conversation
        continuation_prompt: Optional prompt for steering continued conversation
        tags: Optional tags for new conversation
    """

    # Initialize conversation manager
    conv_manager = PersistentConversationManager(db)

    # Get settings for model info
    settings = get_settings()

    # Setup based on mode
    if conversation_mode == 'new':
        # Start new conversation
        print("\n" + "="*60)
        print("Starting New Conversation")
        print("="*60)
        print(f"Title: {title}")
        print(f"Agents: {config['agent_a']['name']} ↔ {config['agent_b']['name']}")

        # Show model info for each agent
        agent_a_model = settings.get_agent_model('agent_a')
        agent_b_model = settings.get_agent_model('agent_b')
        agent_a_display = CostCalculator._get_display_name(agent_a_model)
        agent_b_display = CostCalculator._get_display_name(agent_b_model)

        print(f"\nModels:")
        print(f"  {config['agent_a']['name']}: {agent_a_display}")
        print(f"  {config['agent_b']['name']}: {agent_b_display}")

        # Show pricing info
        agent_a_pricing = CostCalculator.get_model_pricing(agent_a_model)
        agent_b_pricing = CostCalculator.get_model_pricing(agent_b_model)
        print(f"\nPricing (per million tokens):")
        print(f"  {config['agent_a']['name']}: ${agent_a_pricing[0]:.2f}/${agent_a_pricing[1]:.2f} (in/out)")
        print(f"  {config['agent_b']['name']}: ${agent_b_pricing[0]:.2f}/${agent_b_pricing[1]:.2f} (in/out)")

        print(f"\nMax turns: {config['max_turns']}")
        print("="*60)

        conv_id = conv_manager.start_new_conversation(
            title=title,
            initial_prompt=initial_prompt,
            agent_a_id=config['agent_a']['id'],
            agent_a_name=config['agent_a']['name'],
            agent_b_id=config['agent_b']['id'],
            agent_b_name=config['agent_b']['name'],
            tags=tags
        )

        current_message = initial_prompt
        start_turn = 0

        print(f"\n✅ Conversation created (ID: {conv_id[:8]}...)")

    else:  # continue mode
        # Load existing conversation
        if not conv_manager.load_conversation(conversation_id):
            DisplayFormatter.print_error("Failed to load conversation")
            input("Press Enter to continue...")
            return

        print("\n" + "="*60)
        print("Continuing Conversation")
        print("="*60)

        start_turn = conv_manager.current_turn

        # Prepare continuation message
        if continuation_prompt:
            # User wants to steer in new direction
            context = conv_manager.get_context_for_continuation(window_size=3)
            current_message = f"""{context}

New direction: {continuation_prompt}

Please respond considering both the previous context and this new direction."""
            print(f"\n🎯 Steering conversation: {continuation_prompt}")
        else:
            # Continue with original topic
            current_message = conv_manager.get_context_for_continuation(window_size=5)
            print(f"\n▶️  Continuing from turn {start_turn}")

        print("="*60)

    # Get user confirmation
    response = input("\nReady to start? [Y/n]: ").strip().lower()
    if response and response != 'y':
        print("Cancelled.")
        return

    # Create agents (dynamic or static)
    DisplayFormatter.print_info("Initializing agents...")
    pool = AgentPool()
    agents_profiles = []  # Track AgentProfile objects for rating

    try:
        # Dynamic agent creation if coordinator available
        if agent_coordinator:
            # Extract topic from title or initial_prompt
            topic = title or initial_prompt or "General discussion"

            # Get or create dynamic agents
            print("\n🔍 Analyzing topic and selecting experts...")
            agents_profiles, metadata = asyncio.run(
                agent_coordinator.get_or_create_agents(topic)
            )

            if not agents_profiles:
                raise Exception("Could not create agents for this topic")

            # Create Agent objects from profiles
            agents = []
            for profile in agents_profiles:
                # Extract agent_id from the file path (relative to .claude/agents/, without .md)
                agent_id = profile.agent_file_path.replace('.claude/agents/', '').replace('.md', '')
                agent = pool.create_agent(agent_id, profile.name)
                agents.append(agent)

            print(f"\n✅ Using {len(agents)} dynamic agents:")
            for profile in agents_profiles:
                print(f"   • {profile.name} ({profile.domain.value})")

        else:
            # Fallback to static agents (Nova & Atlas)
            print("\n⚠️  Using static agents (dynamic system unavailable)")
            agent_a = pool.create_agent(
                config['agent_a']['id'],
                config['agent_a']['name']
            )
            agent_b = pool.create_agent(
                config['agent_b']['id'],
                config['agent_b']['name']
            )
            agents = [agent_a, agent_b]

        if not pool.validate_all_agents():
            DisplayFormatter.print_error("Agent validation failed!")
            return
    except Exception as e:
        DisplayFormatter.print_error(f"Error creating agents: {e}")
        import traceback
        traceback.print_exc()
        return

    # Setup rich contextual intelligence if available
    metadata_extractor = None
    dashboard = None

    if RICH_CONTEXT_AVAILABLE:
        try:
            # Try to initialize metadata extractor with OpenAI key from settings
            settings = get_settings()
            openai_key = settings.get_openai_api_key()

            if openai_key:
                metadata_extractor = MetadataExtractor(api_key=openai_key)
                dashboard = TerminalDashboard()
                DisplayFormatter.print_success("✨ AI-powered contextual intelligence enabled")
            else:
                DisplayFormatter.print_info("💡 Configure OpenAI key in Settings for rich AI context")
        except Exception as e:
            DisplayFormatter.print_info(f"💡 Rich context unavailable: {e}")

    # Setup interrupt handler for Ctrl-C
    interrupt_handler = ConversationInterruptHandler(
        metadata_extractor=metadata_extractor,
        dashboard=dashboard
    )
    interrupt_handler.install_handler()

    # Show helpful hint
    print("\n💡 Tip: Press Ctrl-C anytime to pause and view conversation context\n")

    # Run conversation (agents already created above)
    current_agent_idx = start_turn % len(agents)  # Resume with correct agent

    total_tokens = 0
    total_cost = 0.0

    try:
        for turn in range(start_turn, start_turn + config['max_turns']):
            # Check for interrupt before starting turn
            if interrupt_handler.check_interrupt():
                action, injected_content = interrupt_handler.show_interrupt_menu(
                    conv_manager, turn, total_tokens, total_cost
                )
                if action == 'stop':
                    # User chose to stop - break out of conversation loop
                    break
                elif action == 'inject':
                    # User injected content
                    print(f"\n{'='*60}")
                    print("💬 CONTENT INJECTION")
                    print(f"{'='*60}")

                    # Add injection to conversation manager
                    result = conv_manager.inject_user_content(injected_content)
                    print(result)

                    # Update the context to include the injection
                    context = conv_manager.get_context_for_continuation(window_size=5)
                    current_message = f"""{context}

Please respond to continue the discussion."""

                    print(f"\n✅ Next agent will see and incorporate this content...")
                    print(f"{'='*60}\n")
                # Continue with this turn (whether resumed or after injection)

            current_agent = agents[current_agent_idx]

            # Display turn header
            DisplayFormatter.print_turn_header(turn, current_agent.agent_name)

            # Get streaming response
            try:
                response_text, token_info = DisplayFormatter.print_streaming_agent_response(
                    current_agent,
                    current_message,
                    show_thinking=config['show_thinking']
                )

                tokens = token_info.get('total_tokens', 0)
                input_tokens = token_info.get('input_tokens', 0)
                output_tokens = token_info.get('output_tokens', 0)
                thinking_tokens = token_info.get('thinking_tokens', 0)
                model_name = token_info.get('model_name')
                temperature = token_info.get('temperature', 1.0)
                max_tokens_setting = token_info.get('max_tokens', 0)

                total_tokens += tokens

                # Calculate cost for this turn
                turn_cost = 0.0
                if model_name and input_tokens > 0:
                    cost_info = CostCalculator.calculate_cost(model_name, input_tokens, output_tokens)
                    turn_cost = cost_info['total_cost']
                    total_cost += turn_cost

                # Choose stats display based on config
                stats_mode = config.get('stats_mode', 'simple')

                if stats_mode == 'geeky':
                    # Collect context statistics
                    context_text = conv_manager.get_context_for_continuation(window_size=5)
                    context_stats = {
                        'total_exchanges': len(conv_manager.exchanges),
                        'window_size': 5,
                        'context_chars': len(context_text),
                        'context_tokens_estimate': len(context_text) // 4,  # Rough estimate
                        'referenced_turns': list(range(max(0, len(conv_manager.exchanges) - 5), len(conv_manager.exchanges)))
                    }

                    # Calculate session statistics
                    session_turns = turn - start_turn + 1
                    avg_tokens = total_tokens // session_turns if session_turns > 0 else 0
                    remaining_turns = (start_turn + config['max_turns']) - turn - 1
                    projected_total = total_tokens + (avg_tokens * remaining_turns)
                    projected_cost = total_cost * (projected_total / total_tokens) if total_tokens > 0 else 0

                    session_stats = {
                        'current_turn': turn + 1,
                        'max_turns': start_turn + config['max_turns'],
                        'avg_tokens_per_turn': avg_tokens,
                        'projected_total_tokens': projected_total,
                        'projected_total_cost': projected_cost
                    }

                    # Model configuration
                    model_config = {
                        'temperature': temperature,
                        'max_tokens': max_tokens_setting
                    }

                    # Display technical stats
                    DisplayFormatter.print_technical_stats(
                        turn_tokens=tokens,
                        total_tokens=total_tokens,
                        model_name=model_name or 'Unknown',
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        thinking_tokens=thinking_tokens,
                        turn_cost=turn_cost,
                        total_cost=total_cost,
                        context_stats=context_stats,
                        session_stats=session_stats,
                        model_config=model_config
                    )
                else:
                    # Simple or detailed mode - use standard display
                    DisplayFormatter.print_token_stats(
                        tokens, total_tokens,
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        turn_cost=turn_cost,
                        total_cost=total_cost
                    )

                # Save to database
                conv_manager.add_exchange(
                    agent_name=current_agent.agent_name,
                    response_content=response_text,
                    thinking_content=None,  # TODO: Capture thinking separately
                    tokens_used=tokens
                )

                # Save periodic snapshots
                if turn % 5 == 0:
                    conv_manager.save_snapshot()

                # Extract metadata periodically (every 3 turns) if available
                if metadata_extractor and turn % 3 == 0:
                    interrupt_handler.extract_metadata_if_available(conv_manager, turn)

                # Prepare message for next agent
                context = conv_manager.get_context_for_continuation(window_size=5)
                current_message = f"""{context}

Please respond to continue the discussion."""

                # Switch to next agent (cycle through all agents)
                current_agent_idx = (current_agent_idx + 1) % len(agents)

            except KeyboardInterrupt:
                raise  # Re-raise to handle in outer try/except
            except Exception as e:
                DisplayFormatter.print_error(f"Error getting response: {e}")
                break

        # Conversation complete
        print("\n" + "="*60)
        print("Conversation Complete")
        print("="*60)
        session_turns = turn - start_turn + 1
        if start_turn == 0:
            print(f"Total turns: {session_turns}")
        else:
            print(f"Turns {start_turn}-{turn} ({session_turns} turns this session)")
        print(f"Total tokens this session: {total_tokens:,}")

        # Show cost summary
        if total_cost > 0:
            cost_str = CostCalculator.format_cost(total_cost)
            print(f"Total cost this session: {cost_str}")

        # Finalize
        conv_manager.finalize_conversation(status='completed')

        print("\n✅ Conversation saved to database")
        print(f"   ID: {conv_manager.conversation_id}")
        print("="*60)

        # Phase 2: Rating and leaderboard (only if using dynamic agents)
        if agent_coordinator and agents_profiles:
            try:
                print("\n" + "━"*60)
                print("📊 PERFORMANCE EVALUATION")
                print("━"*60)

                # Get agent IDs from profiles (relative to .claude/agents/, without .md)
                agent_ids = [profile.agent_file_path.replace('.claude/agents/', '').replace('.md', '')
                            for profile in agents_profiles]

                # Rate agents interactively
                promotions = asyncio.run(
                    agent_coordinator.rate_agents_interactive(
                        agent_ids,
                        conv_manager.conversation_id
                    )
                )

                # Display leaderboard
                print("\n" + "━"*60)
                leaderboard = agent_coordinator.get_leaderboard(top_n=10)
                DisplayFormatter.print_leaderboard(leaderboard, "🏆 Top Performing Agents")

                # Display system statistics
                stats = agent_coordinator.get_statistics()
                print(f"\n📈 System Statistics:")
                print(f"  • Total Agents: {stats['total_agents']}")
                print(f"  • Total Conversations: {stats['total_conversations']}")
                print(f"  • Average Rating: {stats['avg_rating']:.2f}/5.00")
                print(f"  • Total System Cost: ${stats['total_cost']:.4f}")

                # Show rank distribution
                print(f"\n📊 Agents by Rank:")
                for rank_name, count in stats['by_rank'].items():
                    if count > 0:
                        print(f"     {rank_name}: {count}")

                print("━"*60)

            except Exception as e:
                print(f"\n⚠️  Error during rating: {e}")
                import traceback
                traceback.print_exc()

        input("\nPress Enter to return to menu...")

    except KeyboardInterrupt:
        print("\n")
        DisplayFormatter.print_warning("Conversation interrupted by user")
        session_turns = turn - start_turn
        if start_turn == 0:
            print(f"\nℹ️  Completed {session_turns} turns before interruption (interrupted at turn {turn})")
        else:
            print(f"\nℹ️  Interrupted at turn {turn} ({session_turns} turns this session)")
        print(f"💰 Total tokens used: {total_tokens:,}")

        # Show cost summary
        if total_cost > 0:
            cost_str = CostCalculator.format_cost(total_cost)
            print(f"💵 Total cost: {cost_str}")

        # Save interrupted conversation as paused
        conv_manager.finalize_conversation(status='paused')
        print("\n✅ Progress saved. You can continue this conversation later.")

        input("\nPress Enter to return to menu...")

    finally:
        # Always restore the original signal handler
        interrupt_handler.restore_handler()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
