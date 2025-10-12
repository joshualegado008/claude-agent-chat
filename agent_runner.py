"""
Agent Runner - Manages individual Claude agent instances via Anthropic API

This refactored version uses the Anthropic API directly instead of subprocess calls,
creating truly independent agent instances with their own conversation contexts.
"""

import os
import anthropic
from pathlib import Path
from typing import List, Dict, Optional
from conversation_manager import Message
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AgentRunner:
    """
    Manages agent execution using the Anthropic API directly.

    This creates truly independent Claude instances, each with their own
    system prompts and conversation history.
    """

    def __init__(self, config: Dict):
        """
        Initialize the agent runner with configuration.

        Args:
            config: Configuration dictionary (from config.yaml)
        """
        self.config = config
        self.timeout = 120  # 2 minutes default timeout

        # Initialize Anthropic client
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set.\n"
                "Get your API key from: https://console.anthropic.com/\n"
                "Then set it: export ANTHROPIC_API_KEY='sk-ant-...'"
            )

        self.client = anthropic.Anthropic(api_key=api_key)

        # Load agent system prompts
        self.agent_prompts = {}
        for agent_id in config.get('agents', {}).keys():
            self.agent_prompts[agent_id] = self._load_agent_prompt(agent_id)

        # Track conversation history per agent
        self.agent_histories: Dict[str, List[Dict[str, str]]] = {}

    def _load_agent_prompt(self, agent_id: str) -> str:
        """Load an agent's system prompt from their markdown file."""
        agent_file = Path('.claude') / 'agents' / f'{agent_id}.md'

        if not agent_file.exists():
            raise FileNotFoundError(
                f"Agent file not found: {agent_file}\n"
                f"Please create {agent_file} with the agent's personality and instructions."
            )

        with open(agent_file, 'r', encoding='utf-8') as f:
            return f.read()

    def send_message_to_agent(
        self,
        agent_id: str,
        context_messages: List[Message],
        new_message: str
    ) -> Optional[str]:
        """
        Send a message to an agent with context and get response.

        Args:
            agent_id: The agent identifier (e.g., 'agent_a', 'agent_b')
            context_messages: Previous conversation context
            new_message: The new message to send

        Returns:
            The agent's response text, or None if failed
        """
        try:
            # Build conversation history for this agent
            messages = self._build_messages(context_messages, new_message)

            # Get agent's system prompt
            system_prompt = self.agent_prompts.get(agent_id)
            if not system_prompt:
                raise ValueError(f"No system prompt found for agent: {agent_id}")

            # Get model configuration
            agent_config = self.config.get('agents', {}).get(agent_id, {})
            model = agent_config.get('model', 'claude-sonnet-4-5-20250929')
            max_tokens = agent_config.get('max_tokens', 2048)
            temperature = agent_config.get('temperature', 1.0)

            # Make API call
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )

            # Extract response text
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            # Log token usage if debug enabled
            if self.config.get('logging', {}).get('debug', False):
                print(f"[DEBUG] Agent {agent_id} tokens: "
                      f"in={response.usage.input_tokens} "
                      f"out={response.usage.output_tokens}")

            return response_text.strip()

        except anthropic.APIError as e:
            error_msg = f"API Error for agent {agent_id}: {str(e)}"
            print(f"❌ {error_msg}")
            return None
        except Exception as e:
            error_msg = f"Error communicating with agent {agent_id}: {str(e)}"
            print(f"❌ {error_msg}")
            return None

    def _build_messages(
        self,
        context_messages: List[Message],
        new_message: str
    ) -> List[Dict[str, str]]:
        """
        Build the messages array for the API call.

        Converts the context messages and new message into the format
        expected by the Anthropic API.

        Args:
            context_messages: Previous conversation context
            new_message: The new message to send

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = []

        # Add context messages
        if context_messages:
            # Build a summary of the context
            context_text = "=== CONVERSATION CONTEXT ===\n\n"

            for msg in context_messages:
                if msg.is_checkpoint:
                    context_text += f"\n📍 CHECKPOINT:\n{msg.content}\n\n"
                elif msg.is_summary:
                    context_text += f"\n📝 SUMMARY:\n{msg.content}\n\n"
                else:
                    speaker = msg.agent_id or "Agent"
                    context_text += f"{speaker}: {msg.content}\n\n"

            context_text += "=== END CONTEXT ===\n\n"

            # Add context as first user message
            messages.append({
                "role": "user",
                "content": context_text + "Current message:\n" + new_message
            })
        else:
            # No context, just the new message
            messages.append({
                "role": "user",
                "content": new_message
            })

        return messages

    def test_agent_availability(self, agent_id: str) -> bool:
        """
        Test if an agent is available and can respond.

        Args:
            agent_id: The agent identifier

        Returns:
            True if agent is available, False otherwise
        """
        try:
            # Check if agent file exists
            agent_file = Path('.claude') / 'agents' / f'{agent_id}.md'
            if not agent_file.exists():
                print(f"❌ Agent file not found: {agent_file}")
                return False

            # Check if API key is set
            if not os.environ.get('ANTHROPIC_API_KEY'):
                print("❌ ANTHROPIC_API_KEY environment variable not set")
                return False

            # Try a simple API call to validate
            system_prompt = self._load_agent_prompt(agent_id)
            test_response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=10,
                system=system_prompt,
                messages=[{"role": "user", "content": "test"}]
            )

            return True

        except Exception as e:
            print(f"❌ Agent {agent_id} validation failed: {str(e)}")
            return False

    def send_message_streaming(
        self,
        agent_id: str,
        context_messages: List[Message],
        new_message: str,
        enable_thinking: bool = True,
        thinking_budget: int = 5000
    ):
        """
        Send a message to an agent with streaming and optional extended thinking.

        Args:
            agent_id: The agent identifier (e.g., 'agent_a', 'agent_b')
            context_messages: Previous conversation context
            new_message: The new message to send
            enable_thinking: Whether to show extended thinking
            thinking_budget: Maximum tokens for thinking (default 5000)

        Yields:
            Tuples of (content_type, chunk, token_info) where:
            - content_type: 'thinking' or 'text'
            - chunk: Text chunk to display
            - token_info: Dict with token usage info (only on final chunk)
        """
        try:
            # Build conversation history for this agent
            messages = self._build_messages(context_messages, new_message)

            # Get agent's system prompt
            system_prompt = self.agent_prompts.get(agent_id)
            if not system_prompt:
                raise ValueError(f"No system prompt found for agent: {agent_id}")

            # Get model configuration
            agent_config = self.config.get('agents', {}).get(agent_id, {})
            model = agent_config.get('model', 'claude-sonnet-4-5-20250929')
            max_tokens = agent_config.get('max_tokens', 2048)
            temperature = agent_config.get('temperature', 1.0)

            # Build thinking configuration
            thinking_config = {}
            if enable_thinking and 'sonnet-4' in model.lower():
                thinking_config = {
                    'type': 'enabled',
                    'budget_tokens': thinking_budget
                }

            # Stream the response
            thinking_text = ""
            response_text = ""
            input_tokens = 0
            output_tokens = 0

            with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                thinking=thinking_config if thinking_config else None
            ) as stream:
                for event in stream:
                    # Handle thinking blocks
                    if hasattr(event, 'type') and event.type == 'content_block_start':
                        if hasattr(event, 'content_block') and hasattr(event.content_block, 'type'):
                            if event.content_block.type == 'thinking':
                                # Signal start of thinking
                                yield ('thinking_start', '', {})

                    elif hasattr(event, 'type') and event.type == 'content_block_delta':
                        if hasattr(event, 'delta'):
                            if hasattr(event.delta, 'type'):
                                if event.delta.type == 'thinking_delta':
                                    # Yield thinking chunks
                                    if hasattr(event.delta, 'thinking'):
                                        thinking_text += event.delta.thinking
                                        yield ('thinking', event.delta.thinking, {})
                                elif event.delta.type == 'text_delta':
                                    # Yield text chunks
                                    if hasattr(event.delta, 'text'):
                                        response_text += event.delta.text
                                        yield ('text', event.delta.text, {})

                # Get final message with token usage
                final_message = stream.get_final_message()
                if final_message and hasattr(final_message, 'usage'):
                    input_tokens = final_message.usage.input_tokens
                    output_tokens = final_message.usage.output_tokens

            # Yield final token info
            token_info = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'thinking_text': thinking_text,
                'response_text': response_text
            }
            yield ('complete', '', token_info)

            # Log token usage if debug enabled
            if self.config.get('logging', {}).get('debug', False):
                print(f"[DEBUG] Agent {agent_id} tokens: "
                      f"in={input_tokens} out={output_tokens}")

        except anthropic.APIError as e:
            error_msg = f"API Error for agent {agent_id}: {str(e)}"
            print(f"❌ {error_msg}")
            yield ('error', error_msg, {})
        except Exception as e:
            error_msg = f"Error communicating with agent {agent_id}: {str(e)}"
            print(f"❌ {error_msg}")
            yield ('error', error_msg, {})

    def get_agent_stats(self, agent_id: str) -> Dict:
        """
        Get statistics for an agent.

        Args:
            agent_id: The agent identifier

        Returns:
            Dictionary with agent statistics
        """
        history_length = len(self.agent_histories.get(agent_id, []))

        return {
            'agent_id': agent_id,
            'history_length': history_length,
            'has_system_prompt': agent_id in self.agent_prompts
        }
