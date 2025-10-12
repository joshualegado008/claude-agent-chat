"""
Conversation Manager - Advanced context management for agent-to-agent conversations

Implements multi-tier memory management:
- Immediate context: Last N exchanges (always included)
- Checkpoints: Original question + milestone markers
- Summarized history: Condensed older exchanges
"""

import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class MessageRole(Enum):
    """Message role in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Represents a single message in the conversation"""
    role: MessageRole
    content: str
    agent_id: Optional[str] = None
    timestamp: Optional[str] = None
    tokens_estimate: Optional[int] = None
    is_checkpoint: bool = False
    is_summary: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.tokens_estimate is None:
            # Rough estimate: ~4 characters per token
            self.tokens_estimate = len(self.content) // 4

    def to_dict(self):
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['role'] = self.role.value
        return d


@dataclass
class Exchange:
    """Represents a complete exchange between two agents"""
    turn_number: int
    speaker: str
    message: Message
    context_provided: List[Message]
    timestamp: str

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'turn_number': self.turn_number,
            'speaker': self.speaker,
            'message': self.message.to_dict(),
            'context_provided': [msg.to_dict() for msg in self.context_provided],
            'timestamp': self.timestamp
        }


class Summarizer:
    """Handles summarization of conversation history"""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4

    @staticmethod
    def create_simple_summary(messages: List[Message]) -> str:
        """Create a simple summary of messages"""
        if not messages:
            return ""

        summary_parts = []
        for msg in messages:
            agent = msg.agent_id or "Agent"
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"- {agent}: {content_preview}")

        return "Previous discussion:\n" + "\n".join(summary_parts)

    @staticmethod
    def create_recursive_summary(messages: List[Message], previous_summary: Optional[str] = None) -> str:
        """
        Create recursive summary - condenses messages while maintaining context
        Based on research: combines previous summary with new messages
        """
        if not messages:
            return previous_summary or ""

        summary_text = ""

        if previous_summary:
            summary_text = f"Earlier discussion summary:\n{previous_summary}\n\n"

        summary_text += "Recent exchanges:\n"
        for msg in messages:
            agent = msg.agent_id or "Agent"
            # Extract key points (simplified - in production would use LLM)
            content_summary = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
            summary_text += f"- {agent}: {content_summary}\n"

        return summary_text


class CheckpointManager:
    """Manages checkpoints in conversation history"""

    def __init__(self, checkpoint_interval: int = 5):
        self.checkpoint_interval = checkpoint_interval

    def should_create_checkpoint(self, turn_number: int) -> bool:
        """Determine if checkpoint should be created at this turn"""
        return turn_number > 0 and turn_number % self.checkpoint_interval == 0

    def create_checkpoint_message(self, exchanges: List[Exchange], turn_number: int) -> Message:
        """Create a checkpoint message summarizing recent progress"""
        recent_exchanges = [ex for ex in exchanges if ex.turn_number > turn_number - self.checkpoint_interval]

        checkpoint_content = f"[CHECKPOINT - Turn {turn_number}]\n"
        checkpoint_content += f"Recent discussion points:\n"

        for ex in recent_exchanges[-3:]:  # Last 3 exchanges
            agent = ex.speaker
            preview = ex.message.content[:100] + "..." if len(ex.message.content) > 100 else ex.message.content
            checkpoint_content += f"- {agent}: {preview}\n"

        return Message(
            role=MessageRole.SYSTEM,
            content=checkpoint_content,
            is_checkpoint=True,
            timestamp=datetime.now().isoformat()
        )


class ContextBuilder:
    """Builds optimized context for agent messages"""

    def __init__(self, config: Dict):
        self.immediate_exchanges = config.get('immediate_exchanges', 3)
        self.summarize_after = config.get('summarize_after', 6)
        self.preserve_original = config.get('preserve_original', True)
        self.max_context_tokens = config.get('max_context_tokens', 8000)
        self.summarization_strategy = config.get('summarization_strategy', 'recursive')
        self.summarizer = Summarizer()

    def build_context(self, exchanges: List[Exchange], original_prompt: str,
                     checkpoints: List[Message]) -> List[Message]:
        """
        Build optimized context for the next agent message

        Strategy:
        1. Always include original prompt (if preserve_original)
        2. Include relevant checkpoints
        3. Include summarized older history (if needed)
        4. Always include last N exchanges in full
        """
        context = []
        total_tokens = 0

        # 1. Original prompt (anchor point)
        if self.preserve_original and original_prompt:
            original_msg = Message(
                role=MessageRole.SYSTEM,
                content=f"Original conversation topic:\n{original_prompt}",
                is_checkpoint=True
            )
            context.append(original_msg)
            total_tokens += original_msg.tokens_estimate

        # 2. Get immediate (recent) exchanges
        immediate_start = max(0, len(exchanges) - self.immediate_exchanges)
        immediate_exchanges = exchanges[immediate_start:]
        older_exchanges = exchanges[:immediate_start]

        # 3. Handle older exchanges - summarize if needed
        if len(exchanges) > self.summarize_after and older_exchanges:
            summary_text = self._create_summary(older_exchanges)
            summary_msg = Message(
                role=MessageRole.SYSTEM,
                content=summary_text,
                is_summary=True
            )
            context.append(summary_msg)
            total_tokens += summary_msg.tokens_estimate

        # 4. Add relevant checkpoints (if not too many tokens)
        for checkpoint in checkpoints[-2:]:  # Last 2 checkpoints
            if total_tokens + checkpoint.tokens_estimate < self.max_context_tokens:
                context.append(checkpoint)
                total_tokens += checkpoint.tokens_estimate

        # 5. Add immediate exchanges (always included, even if over token limit)
        for exchange in immediate_exchanges:
            context.append(exchange.message)
            total_tokens += exchange.message.tokens_estimate

        return context

    def _create_summary(self, exchanges: List[Exchange]) -> str:
        """Create summary of older exchanges"""
        messages = [ex.message for ex in exchanges]

        if self.summarization_strategy == 'recursive':
            # TODO: Implement true recursive summarization with previous summaries
            return self.summarizer.create_recursive_summary(messages)
        else:
            return self.summarizer.create_simple_summary(messages)


class ConversationHistory:
    """Manages the full conversation history with metadata"""

    def __init__(self, config: Dict, initial_prompt: str):
        self.config = config
        self.initial_prompt = initial_prompt
        self.exchanges: List[Exchange] = []
        self.checkpoints: List[Message] = []
        self.current_turn = 0

        self.context_builder = ContextBuilder(config.get('context', {}))
        self.checkpoint_manager = CheckpointManager(
            config.get('context', {}).get('checkpoint_interval', 5)
        )

    def add_exchange(self, speaker: str, message_content: str,
                    context_provided: List[Message]) -> Exchange:
        """Add a new exchange to the history"""
        message = Message(
            role=MessageRole.ASSISTANT,
            content=message_content,
            agent_id=speaker,
            timestamp=datetime.now().isoformat()
        )

        exchange = Exchange(
            turn_number=self.current_turn,
            speaker=speaker,
            message=message,
            context_provided=context_provided,
            timestamp=datetime.now().isoformat()
        )

        self.exchanges.append(exchange)
        self.current_turn += 1

        # Check if we should create a checkpoint
        if self.checkpoint_manager.should_create_checkpoint(self.current_turn):
            checkpoint = self.checkpoint_manager.create_checkpoint_message(
                self.exchanges, self.current_turn
            )
            self.checkpoints.append(checkpoint)

        return exchange

    def build_context_for_next_turn(self) -> List[Message]:
        """Build optimized context for the next agent"""
        return self.context_builder.build_context(
            self.exchanges,
            self.initial_prompt,
            self.checkpoints
        )

    def get_total_tokens(self) -> int:
        """Estimate total tokens used in conversation"""
        return sum(ex.message.tokens_estimate for ex in self.exchanges)

    def to_dict(self) -> Dict:
        """Convert entire history to dictionary for serialization"""
        return {
            'initial_prompt': self.initial_prompt,
            'current_turn': self.current_turn,
            'total_tokens': self.get_total_tokens(),
            'exchanges': [ex.to_dict() for ex in self.exchanges],
            'checkpoints': [cp.to_dict() for cp in self.checkpoints],
            'timestamp': datetime.now().isoformat()
        }

    def save_to_json(self, filepath: str):
        """Save conversation history to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def save_to_markdown(self, filepath: str):
        """Save conversation transcript to Markdown file"""
        with open(filepath, 'w') as f:
            f.write(f"# Agent Conversation Transcript\n\n")
            f.write(f"**Initial Prompt:** {self.initial_prompt}\n\n")
            f.write(f"**Total Turns:** {self.current_turn}\n")
            f.write(f"**Estimated Tokens:** {self.get_total_tokens()}\n\n")
            f.write("---\n\n")

            for exchange in self.exchanges:
                f.write(f"## Turn {exchange.turn_number} - {exchange.speaker}\n\n")
                f.write(f"*{exchange.timestamp}*\n\n")
                f.write(f"{exchange.message.content}\n\n")
                f.write("---\n\n")
