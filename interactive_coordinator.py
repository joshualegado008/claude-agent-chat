"""
Interactive Coordinator - Conversation system with CTRL-C interrupt support and rich metadata
"""

import os
import sys
import json
import signal
import asyncio
from datetime import datetime
from typing import Optional, Dict

from agent_runner import AgentPool
from display_formatter import DisplayFormatter
from db_manager import DatabaseManager
from conversation_manager_persistent import PersistentConversationManager
from metadata_extractor import MetadataExtractor
from terminal_dashboard import TerminalDashboard
from settings_manager import get_settings
from search_coordinator import SearchCoordinator


class InteractiveCoordinator:
    """Manages conversations with CTRL-C interrupt support for viewing metadata."""

    def __init__(self, db: DatabaseManager):
        self.db = db

        # Load config for search coordinator
        import yaml
        from pathlib import Path
        config_path = Path('config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        # Initialize metadata extractor with key from settings
        settings = get_settings()
        openai_key = settings.get_openai_api_key()
        self.metadata_extractor = MetadataExtractor(api_key=openai_key)

        # Initialize search coordinator if search is enabled in config
        search_config = self.config.get('search', {})
        if search_config.get('enabled', False):
            try:
                self.search_coordinator = SearchCoordinator(self.config)
                print("✅ Autonomous search enabled")
            except Exception as e:
                print(f"⚠️  Failed to initialize search coordinator: {e}")
                self.search_coordinator = None
        else:
            self.search_coordinator = None

        self.dashboard = TerminalDashboard()
        self.conversation_paused = False
        self.current_metadata = None
        self.interrupt_requested = False
        self.original_sigint_handler = None

    def _signal_handler(self, signum, frame):
        """Handle CTRL-C (SIGINT) gracefully by setting interrupt flag."""
        self.interrupt_requested = True
        # Don't print here - let _handle_interrupt do the display

    def _check_for_interrupt(self) -> bool:
        """
        Check if user pressed CTRL-C to interrupt.

        Returns:
            True if interrupt detected
        """
        if self.interrupt_requested:
            self.interrupt_requested = False
            return True
        return False

    def start_new_conversation_streamlined(
        self,
        title: str,
        config: dict
    ) -> Optional[str]:
        """
        Start a new conversation with streamlined input.

        Args:
            title: Conversation title (used to generate prompt and tags)
            config: Configuration dict

        Returns:
            conversation_id if successful
        """
        print("\n" + "="*60)
        print(f"{DisplayFormatter.print_info('Analyzing conversation topic...')}")

        # Generate initial prompt from title
        initial_prompt = self.metadata_extractor.generate_initial_prompt(title)
        print(f"\n✨ Generated Prompt:")
        print(f"   {initial_prompt}\n")

        # Extract tags
        tags = self.metadata_extractor.extract_tags_from_title(title)
        print(f"🏷️  Auto-generated Tags: {', '.join(tags)}\n")

        # Create conversation
        conv_manager = PersistentConversationManager(self.db)
        conversation_id = conv_manager.start_new_conversation(
            title=title,
            initial_prompt=initial_prompt,
            agent_a_id=config['agent_a']['id'],
            agent_a_name=config['agent_a']['name'],
            agent_b_id=config['agent_b']['id'],
            agent_b_name=config['agent_b']['name'],
            tags=tags
        )

        print("="*60)
        print(f"Title: {title}")
        print(f"Agents: {config['agent_a']['name']} ↔ {config['agent_b']['name']}")
        print(f"Max turns: {config['max_turns']}")
        print("="*60)
        print(f"\n✅ Conversation created (ID: {conversation_id[:8]}...)\n")

        # Show help hint
        self.dashboard.show_help_hint()

        # Confirm start
        response = input("Ready to start? [Y/n]: ").strip().lower()
        if response and response != 'y':
            print("Cancelled.")
            return None

        # Run the conversation
        self._run_conversation_with_metadata(
            conv_manager=conv_manager,
            initial_prompt=initial_prompt,
            config=config
        )

        return conversation_id

    def _run_conversation_with_metadata(
        self,
        conv_manager: PersistentConversationManager,
        initial_prompt: str,
        config: dict
    ):
        """Run conversation with metadata extraction and CTRL-C interrupt support."""

        # Install CTRL-C handler
        self.original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)

        try:
            # Create agents
            pool = AgentPool()
            agent_a = pool.create_agent(config['agent_a']['id'], config['agent_a']['name'])
            agent_b = pool.create_agent(config['agent_b']['id'], config['agent_b']['name'])

            agents = [agent_a, agent_b]
            current_message = initial_prompt
            current_agent_idx = 0
            total_tokens = 0

            # Metadata tracking
            last_metadata_turn = -1
            metadata_interval = 3  # Analyze every 3 turns

            for turn in range(config['max_turns']):
                if self.conversation_paused:
                    # Handle pause state
                    continue

                current_agent = agents[current_agent_idx]

                # Display turn header
                DisplayFormatter.print_turn_header(turn, current_agent.agent_name)

                # Check for interrupt before agent responds
                if self._check_for_interrupt():
                    choice = self._handle_interrupt(
                        conv_manager,
                        turn,
                        total_tokens,
                        config
                    )

                    if choice == 'stop':
                        break
                    elif choice == 'resume':
                        # Continue with current turn
                        pass

                # Get streaming response
                try:
                    thinking_text = ""
                    response_text = ""

                    for content_type, text_chunk, tokens in current_agent.send_message_streaming(
                        current_message,
                        enable_thinking=config['show_thinking']
                    ):
                        # Check for interrupt during streaming
                        if self._check_for_interrupt():
                            choice = self._handle_interrupt(
                                conv_manager,
                                turn,
                                total_tokens,
                                config
                            )
                            if choice == 'stop':
                                raise KeyboardInterrupt

                        if content_type == 'thinking':
                            if not thinking_text:  # First thinking chunk
                                DisplayFormatter.print_thinking_header(current_agent.agent_name)
                            thinking_text += text_chunk
                            DisplayFormatter.stream_thinking(text_chunk)

                        elif content_type == 'response':
                            if not response_text:  # First response chunk
                                if thinking_text:
                                    print()  # New line after thinking
                                DisplayFormatter.print_response_header(current_agent.agent_name)
                            response_text += text_chunk
                            DisplayFormatter.stream_response(text_chunk)

                        elif content_type == 'complete':
                            total_tokens += tokens
                            print()  # New line after response
                            DisplayFormatter.print_token_stats(tokens, total_tokens)

                    # Save exchange
                    conv_manager.add_exchange(
                        agent_name=current_agent.agent_name,
                        response_content=response_text,
                        thinking_content=thinking_text if thinking_text else None,
                        tokens_used=tokens
                    )

                    # Check for autonomous search triggers
                    search_results_text = ""
                    if self.search_coordinator:
                        try:
                            # Check if search should be triggered
                            should_search, trigger_type, query = self.search_coordinator.should_search(
                                response=response_text,
                                thinking=thinking_text,
                                turn_number=turn,
                                agent_name=current_agent.agent_name
                            )

                            if should_search:
                                # Display blue search trigger indicator
                                DisplayFormatter.print_search_triggered(query, trigger_type, current_agent.agent_name)

                                # Execute search (async)
                                search_ctx = asyncio.run(
                                    self.search_coordinator.execute_search(
                                        query=query,
                                        agent_name=current_agent.agent_name,
                                        turn_number=turn,
                                        trigger_type=trigger_type
                                    )
                                )

                                if search_ctx:
                                    # Display green sources found indicator
                                    DisplayFormatter.print_sources_found(
                                        count=len(search_ctx.extracted_content),
                                        sources=[
                                            {
                                                'title': content.title,
                                                'url': content.url,
                                                'publisher': content.site
                                            }
                                            for content in search_ctx.extracted_content
                                        ]
                                    )

                                    # Format search results for injection into next turn
                                    search_results_text = self.search_coordinator.format_search_for_context(search_ctx)

                        except Exception as e:
                            print(f"⚠️  Search error: {e}")

                    # Extract and save metadata periodically
                    if turn - last_metadata_turn >= metadata_interval:
                        self._extract_and_save_metadata(
                            conv_manager,
                            turn,
                            config
                        )
                        last_metadata_turn = turn

                    # Prepare next message (with search results if available)
                    context = conv_manager.get_context_for_continuation(window_size=5)
                    if search_results_text:
                        current_message = f"{context}\n\n{search_results_text}\n\nPlease respond to continue the discussion."
                    else:
                        current_message = f"{context}\n\nPlease respond to continue the discussion."

                    # Switch agents
                    current_agent_idx = 1 - current_agent_idx

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    DisplayFormatter.print_error(f"Error getting response: {e}")
                    break

            # Conversation complete
            print("\n" + "="*60)
            print("Conversation Complete")
            print("="*60)
            print(f"Total turns: {turn + 1}")
            print(f"Total tokens: {total_tokens:,}")

            # Final metadata extraction
            self._extract_and_save_metadata(conv_manager, turn + 1, config)

            # Finalize
            conv_manager.finalize_conversation(status='completed')
            print("\n✅ Conversation saved to database")
            print("="*60)

        except KeyboardInterrupt:
            print("\n")
            DisplayFormatter.print_warning("Conversation interrupted by user")
            conv_manager.finalize_conversation(status='active')
            print("\n✅ Progress saved. You can continue this conversation later.")

        finally:
            # Restore original SIGINT handler
            if self.original_sigint_handler:
                signal.signal(signal.SIGINT, self.original_sigint_handler)

    def _handle_interrupt(
        self,
        conv_manager: PersistentConversationManager,
        current_turn: int,
        total_tokens: int,
        config: dict
    ) -> str:
        """
        Handle conversation interrupt - show menu and process choice.

        Returns:
            Action to take: 'resume', 'stop', etc.
        """
        self.conversation_paused = True

        # Temporarily restore default CTRL-C behavior for menu
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        try:
            choice = self.dashboard.display_interrupt_menu()

            if choice == '1':
                # View stats & context
                self._show_metadata_dashboard(
                    conv_manager,
                    current_turn,
                    total_tokens,
                    config
                )
                input()  # Wait for key press
                return 'resume'

            elif choice == '2':
                # Say something (future feature)
                print(f"\n{DisplayFormatter.print_info('💬 Say Something feature coming soon!')}")
                input("\nPress Enter to continue...")
                return 'resume'

            elif choice == '3':
                # Save snapshot
                # Note: Need to implement save_snapshot in conv_manager
                print(f"\n✅ Snapshot saved at turn {current_turn}")
                input("\nPress Enter to continue...")
                return 'resume'

            elif choice == '4':
                # Stop conversation
                confirm = input(f"\n⚠️  Stop conversation? [y/N]: ").strip().lower()
                if confirm == 'y':
                    return 'stop'
                return 'resume'

            elif choice == '5' or not choice:
                # Resume
                self.conversation_paused = False
                return 'resume'

            else:
                return 'resume'

        finally:
            # Restore our custom SIGINT handler
            signal.signal(signal.SIGINT, self._signal_handler)

    def _extract_and_save_metadata(
        self,
        conv_manager: PersistentConversationManager,
        turn_number: int,
        config: dict
    ):
        """Extract metadata and save to database."""
        try:
            # Get recent exchanges
            recent_exchanges = conv_manager.exchanges[-10:] if conv_manager.exchanges else []

            # Extract metadata
            metadata = self.metadata_extractor.analyze_conversation_snapshot(
                recent_exchanges=recent_exchanges,
                title=conv_manager.metadata.get('title', 'Untitled'),
                total_turns=turn_number
            )

            # Store in memory for dashboard
            self.current_metadata = metadata

            # Save to database
            self._save_metadata_to_db(
                conversation_id=conv_manager.conversation_id,
                turn_number=turn_number,
                metadata=metadata
            )

            # Show compact update
            if config.get('show_metadata_updates', False):
                self.dashboard.display_compact_update(metadata, turn_number)

        except Exception as e:
            print(f"\n⚠️  Metadata extraction failed: {e}")

    def _save_metadata_to_db(
        self,
        conversation_id: str,
        turn_number: int,
        metadata: Dict
    ):
        """Save metadata to PostgreSQL."""
        try:
            with self.db.pg_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO conversation_metadata (
                        conversation_id, snapshot_at_turn, current_vibe,
                        content_type, technical_level, sentiment,
                        conversation_stage, complexity_level, engagement_quality,
                        main_topics, key_concepts, emerging_themes, named_entities
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conversation_id, snapshot_at_turn)
                    DO UPDATE SET
                        current_vibe = EXCLUDED.current_vibe,
                        content_type = EXCLUDED.content_type,
                        technical_level = EXCLUDED.technical_level,
                        sentiment = EXCLUDED.sentiment,
                        conversation_stage = EXCLUDED.conversation_stage,
                        complexity_level = EXCLUDED.complexity_level,
                        engagement_quality = EXCLUDED.engagement_quality,
                        main_topics = EXCLUDED.main_topics,
                        key_concepts = EXCLUDED.key_concepts,
                        emerging_themes = EXCLUDED.emerging_themes,
                        named_entities = EXCLUDED.named_entities
                """, (
                    conversation_id,
                    turn_number,
                    metadata.get('current_vibe'),
                    metadata.get('content_type'),
                    metadata.get('technical_level'),
                    metadata.get('sentiment'),
                    metadata.get('conversation_stage'),
                    metadata.get('complexity_level'),
                    metadata.get('engagement_quality'),
                    metadata.get('main_topics', []),
                    metadata.get('key_concepts', []),
                    metadata.get('emerging_themes', []),
                    json.dumps(metadata.get('named_entities', {}))
                ))
                self.db.pg_conn.commit()
        except Exception as e:
            print(f"⚠️  Failed to save metadata: {e}")

    def _show_metadata_dashboard(
        self,
        conv_manager: PersistentConversationManager,
        current_turn: int,
        total_tokens: int,
        config: dict
    ):
        """Display the full metadata dashboard."""
        # Extract fresh metadata if needed
        if not self.current_metadata:
            recent_exchanges = conv_manager.exchanges[-10:]
            self.current_metadata = self.metadata_extractor.analyze_conversation_snapshot(
                recent_exchanges=recent_exchanges,
                title=conv_manager.metadata.get('title', 'Untitled'),
                total_turns=current_turn
            )

        # Display dashboard
        self.dashboard.display_full_dashboard(
            metadata=self.current_metadata,
            conversation_title=conv_manager.metadata.get('title', 'Untitled'),
            total_turns=current_turn,
            total_tokens=total_tokens
        )
