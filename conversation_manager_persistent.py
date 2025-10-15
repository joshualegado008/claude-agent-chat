"""
Persistent Conversation Manager - Integrates with PostgreSQL and Qdrant
"""

from typing import Dict, List, Optional
from datetime import datetime
from db_manager import DatabaseManager


class PersistentConversationManager:
    """
    Manages conversation state with persistent storage in PostgreSQL and Qdrant.
    Supports continuing previous conversations and semantic search.
    """

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db = db_manager
        self.conversation_id: Optional[str] = None
        self.exchanges: List[Dict] = []
        self.metadata: Dict = {}
        self.current_turn: int = 0

    def start_new_conversation(
        self,
        title: str,
        initial_prompt: str,
        agent_a_id: str = None,
        agent_a_name: str = None,
        agent_b_id: str = None,
        agent_b_name: str = None,
        tags: List[str] = None,
        agents: List[Dict] = None  # New: Array of {id, name, qualification}
    ) -> str:
        """
        Start a new conversation and create database record.

        Supports both legacy 2-agent format and new multi-agent format:
        - Legacy: Pass agent_a_id, agent_a_name, agent_b_id, agent_b_name
        - Multi-agent: Pass agents list with {id, name, qualification} dicts

        Returns:
            conversation_id
        """
        self.conversation_id = self.db.create_conversation(
            title=title,
            initial_prompt=initial_prompt,
            agent_a_id=agent_a_id,
            agent_a_name=agent_a_name,
            agent_b_id=agent_b_id,
            agent_b_name=agent_b_name,
            tags=tags,
            agents=agents
        )

        self.exchanges = []
        self.current_turn = 0

        # Build metadata based on format
        if agents:
            # Multi-agent format
            self.metadata = {
                'title': title,
                'initial_prompt': initial_prompt,
                'agents': agents,
                'created_at': datetime.now().isoformat()
            }
            # Also include agent_a/agent_b for backward compatibility
            if len(agents) >= 1:
                self.metadata['agent_a_id'] = agents[0].get('id')
                self.metadata['agent_a_name'] = agents[0].get('name')
            if len(agents) >= 2:
                self.metadata['agent_b_id'] = agents[1].get('id')
                self.metadata['agent_b_name'] = agents[1].get('name')
        else:
            # Legacy format
            self.metadata = {
                'title': title,
                'initial_prompt': initial_prompt,
                'agent_a_id': agent_a_id,
                'agent_a_name': agent_a_name,
                'agent_b_id': agent_b_id,
                'agent_b_name': agent_b_name,
                'created_at': datetime.now().isoformat()
            }

        return self.conversation_id

    def load_conversation(self, conversation_id: str) -> bool:
        """
        Load an existing conversation from the database.

        Returns:
            True if successful, False if conversation not found
        """
        data = self.db.load_conversation(conversation_id)

        if not data:
            return False

        self.conversation_id = conversation_id
        self.exchanges = data['exchanges']
        self.metadata = data['conversation']
        self.current_turn = len(self.exchanges)

        # Validate and auto-correct status if needed
        current_status = self.metadata.get('status', 'active')
        if self.current_turn >= 20 and current_status == 'active':
            print(f"⚠️  Auto-correcting status: conversation has {self.current_turn} turns but marked as 'active'")
            self.db.update_conversation_stats(
                conversation_id=self.conversation_id,
                total_turns=self.current_turn,
                total_tokens=sum(ex.get('tokens_used', 0) for ex in self.exchanges),
                status='completed'
            )
            self.metadata['status'] = 'completed'
            print(f"   ✅ Status updated to 'completed'")

        # Build agent display string
        if self.metadata.get('agents'):
            # Multi-agent format
            agent_names = [agent['name'] for agent in self.metadata['agents']]
            agents_display = ' ↔ '.join(agent_names)
        else:
            # Legacy 2-agent format
            agents_display = f"{self.metadata.get('agent_a_name', 'Unknown')} ↔ {self.metadata.get('agent_b_name', 'Unknown')}"

        print(f"\n✅ Loaded conversation: {self.metadata['title']}")
        print(f"   Turns: {self.current_turn}")
        print(f"   Status: {self.metadata.get('status', 'active')}")
        print(f"   Created: {self.metadata['created_at']}")
        print(f"   Agents: {agents_display}")

        return True

    def add_exchange(
        self,
        agent_name: str,
        response_content: str,
        thinking_content: Optional[str] = None,
        tokens_used: int = 0
    ):
        """Add an exchange to the conversation and persist to database."""

        if not self.conversation_id:
            raise ValueError("No active conversation. Call start_new_conversation() first.")

        exchange = {
            'turn_number': self.current_turn,
            'agent_name': agent_name,
            'thinking_content': thinking_content,
            'response_content': response_content,
            'tokens_used': tokens_used,
            'created_at': datetime.now().isoformat()
        }

        self.exchanges.append(exchange)

        # Persist to database
        self.db.add_exchange(
            conversation_id=self.conversation_id,
            turn_number=self.current_turn,
            agent_name=agent_name,
            thinking_content=thinking_content,
            response_content=response_content,
            tokens_used=tokens_used
        )

        self.current_turn += 1

    def inject_user_content(self, content: str) -> str:
        """
        Inject user-provided content into the conversation.

        This allows users to add new material (text, questions, URLs) mid-conversation
        that agents will incorporate into their ongoing discussion.

        Args:
            content: The user's injected content

        Returns:
            Formatted message confirming the injection
        """
        if not self.conversation_id:
            raise ValueError("No active conversation. Call start_new_conversation() first.")

        # Create a special USER exchange
        # Use current turn number but mark as USER to distinguish from agent exchanges
        exchange = {
            'turn_number': self.current_turn,
            'agent_name': 'USER',
            'thinking_content': None,
            'response_content': content,
            'tokens_used': 0,  # User injections don't cost tokens
            'created_at': datetime.now().isoformat()
        }

        self.exchanges.append(exchange)

        # Persist to database
        self.db.add_exchange(
            conversation_id=self.conversation_id,
            turn_number=self.current_turn,
            agent_name='USER',
            thinking_content=None,
            response_content=content,
            tokens_used=0
        )

        # Increment turn counter so next agent gets a unique turn number
        injection_turn = self.current_turn
        self.current_turn += 1

        return f"✅ User content injected at turn {injection_turn}"

    def get_context_for_continuation(
        self,
        window_size: int = 5
    ) -> str:
        """
        Get conversation context for continuing a previous conversation.
        Returns recent exchanges formatted for the prompt.

        Handles USER injections by highlighting them prominently in the context.
        """
        if not self.exchanges:
            return self.metadata.get('initial_prompt', '')

        # Get recent exchanges
        recent = self.exchanges[-window_size:] if len(self.exchanges) > window_size else self.exchanges

        context_parts = [
            f"Previous conversation context:",
            f"Initial topic: {self.metadata.get('initial_prompt', 'N/A')}",
            f"\nRecent exchanges:\n"
        ]

        # Track if there are any USER injections
        has_user_injection = False

        for ex in recent:
            agent_name = ex['agent_name']

            if agent_name == 'USER':
                # Highlight user injections prominently
                has_user_injection = True
                context_parts.append(
                    f"\n{'='*60}\n"
                    f"🎯 USER INJECTION (at turn {ex['turn_number']}):\n"
                    f"{ex['response_content']}\n"
                    f"{'='*60}\n"
                )
            else:
                # Regular agent exchange
                content_preview = ex['response_content'][:200]
                if len(ex['response_content']) > 200:
                    content_preview += "..."
                context_parts.append(
                    f"Turn {ex['turn_number']} - {agent_name}: {content_preview}"
                )

        # Add instructions based on whether there's a user injection
        if has_user_injection:
            context_parts.append(
                "\nThe user has added new material to the conversation. Please acknowledge "
                "and incorporate this into your response while maintaining the flow of "
                "the existing discussion."
            )
        else:
            context_parts.append("\nContinue the discussion from here.")

        return "\n".join(context_parts)

    def get_full_history(self) -> str:
        """Get complete conversation history as formatted text."""
        if not self.exchanges:
            return "No exchanges yet."

        history_parts = [
            f"Conversation: {self.metadata.get('title', 'Untitled')}",
            f"Started: {self.metadata.get('created_at', 'N/A')}",
            f"\nInitial prompt: {self.metadata.get('initial_prompt', 'N/A')}\n",
            "="*60
        ]

        for ex in self.exchanges:
            history_parts.append(
                f"\nTurn {ex['turn_number']} - {ex['agent_name']}:"
            )
            if ex.get('thinking_content'):
                history_parts.append(f"💭 Thinking: {ex['thinking_content'][:100]}...")
            history_parts.append(f"{ex['response_content']}\n")

        return "\n".join(history_parts)

    def save_snapshot(self):
        """Save current conversation state as a snapshot."""
        if not self.conversation_id:
            return

        context_data = {
            'exchanges': self.exchanges,
            'metadata': self.metadata,
            'current_turn': self.current_turn
        }

        self.db.save_context_snapshot(
            conversation_id=self.conversation_id,
            turn_number=self.current_turn,
            context_data=context_data
        )

    def finalize_conversation(self, status: str = 'completed'):
        """Mark conversation as complete and update stats."""
        if not self.conversation_id:
            return

        total_tokens = sum(ex.get('tokens_used', 0) for ex in self.exchanges)

        self.db.update_conversation_stats(
            conversation_id=self.conversation_id,
            total_turns=self.current_turn,
            total_tokens=total_tokens,
            status=status
        )

        # Save final snapshot
        self.save_snapshot()


class ConversationBrowser:
    """Browse and search past conversations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def list_recent(self, limit: int = 20) -> List[Dict]:
        """List recent conversations."""
        return self.db.list_conversations(limit=limit)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Semantic search across conversations."""
        return self.db.search_conversations(query=query, limit=limit)

    def display_conversation_list(self, conversations: List[Dict]):
        """Display conversations in a formatted list."""
        if not conversations:
            print("\n❌ No conversations found.")
            return

        print("\n" + "="*80)
        print(f"{'#':<4} {'Title':<30} {'Agents':<20} {'Turns':<7} {'Updated':<20}")
        print("="*80)

        for idx, conv in enumerate(conversations, 1):
            title = conv.get('title', 'Untitled')[:28]
            agents = f"{conv.get('agent_a_name', 'N/A')} ↔ {conv.get('agent_b_name', 'N/A')}"[:18]
            turns = conv.get('total_turns', 0)
            updated = conv.get('updated_at', 'N/A')

            if isinstance(updated, datetime):
                updated = updated.strftime('%Y-%m-%d %H:%M')
            elif isinstance(updated, str):
                updated = updated[:16]

            print(f"{idx:<4} {title:<30} {agents:<20} {turns:<7} {updated:<20}")

        print("="*80)
