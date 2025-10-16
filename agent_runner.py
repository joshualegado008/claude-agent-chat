"""
Agent Runner - Manages individual Claude agent instances via Anthropic API

This refactored version uses the Anthropic API directly instead of subprocess calls,
creating truly independent Claude instances with their own conversation contexts.
"""

import os
import time
import anthropic
from pathlib import Path
from typing import List, Dict, Optional
from conversation_manager import Message
from dotenv import load_dotenv
from settings_manager import get_settings
import web_tools

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
        self.max_retries = 3  # Retry transient network errors up to 3 times
        self.retry_base_delay = 1.0  # Base delay in seconds for exponential backoff
        self.settings = get_settings()

        # Initialize Anthropic client using settings
        api_key = self.settings.get_anthropic_api_key()
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not configured.\n"
                "Get your API key from: https://console.anthropic.com/\n"
                "Configure it via Settings menu or set environment variable:\n"
                "export ANTHROPIC_API_KEY='sk-ant-...'"
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
        # Check both static and dynamic agent directories
        # Static agents: .claude/agents/{agent_id}.md
        # Dynamic agents: .claude/agents/dynamic/{agent_id}.md
        static_path = Path('.claude') / 'agents' / f'{agent_id}.md'
        dynamic_path = Path('.claude') / 'agents' / 'dynamic' / f'{agent_id}.md'

        # Try static path first (for backwards compatibility)
        if static_path.exists():
            agent_file = static_path
        elif dynamic_path.exists():
            agent_file = dynamic_path
        else:
            raise FileNotFoundError(
                f"Agent file not found at:\n"
                f"  {static_path}\n"
                f"  {dynamic_path}\n"
                f"Please create one of these files with the agent's personality and instructions."
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

            # Get agent's system prompt (lazy-load if needed for dynamic agents)
            system_prompt = self.agent_prompts.get(agent_id)
            if not system_prompt:
                # Try to load it from disk (for dynamic agents)
                try:
                    system_prompt = self._load_agent_prompt(agent_id)
                    self.agent_prompts[agent_id] = system_prompt  # Cache it
                except FileNotFoundError:
                    raise ValueError(f"No system prompt found for agent: {agent_id}")

            # Get model configuration from settings first, then fall back to config
            model = self.settings.get_agent_model(agent_id)
            agent_config = self.config.get('agents', {}).get(agent_id, {})
            max_tokens = agent_config.get('max_tokens', 8000)  # Must be > thinking_budget (5000)
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
            # Check if agent file exists (static or dynamic)
            static_path = Path('.claude') / 'agents' / f'{agent_id}.md'
            dynamic_path = Path('.claude') / 'agents' / 'dynamic' / f'{agent_id}.md'

            if not static_path.exists() and not dynamic_path.exists():
                print(f"❌ Agent file not found at {static_path} or {dynamic_path}")
                return False

            # Check if API key is set
            if not os.environ.get('ANTHROPIC_API_KEY'):
                print("❌ ANTHROPIC_API_KEY environment variable not set")
                return False

            # Try a simple API call to validate
            system_prompt = self._load_agent_prompt(agent_id)
            model = self.settings.get_agent_model(agent_id)
            test_response = self.client.messages.create(
                model=model,
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
        Send a message to an agent with streaming, optional extended thinking, and tool support.

        Args:
            agent_id: The agent identifier (e.g., 'agent_a', 'agent_b')
            context_messages: Previous conversation context
            new_message: The new message to send
            enable_thinking: Whether to show extended thinking
            thinking_budget: Maximum tokens for thinking (default 5000)

        Yields:
            Tuples of (content_type, chunk, token_info) where:
            - content_type: 'thinking', 'text', 'tool_use', or 'complete'
            - chunk: Text chunk to display
            - token_info: Dict with token usage info (only on final chunk)
        """
        try:
            # Load web browsing config
            web_config = web_tools.get_web_config(self.config)
            tools_enabled = web_config.get('enabled', False)

            # Build conversation history for this agent
            messages = self._build_messages(context_messages, new_message)

            # Get agent's system prompt (lazy-load if needed for dynamic agents)
            system_prompt = self.agent_prompts.get(agent_id)
            if not system_prompt:
                # Try to load it from disk (for dynamic agents)
                try:
                    system_prompt = self._load_agent_prompt(agent_id)
                    self.agent_prompts[agent_id] = system_prompt  # Cache it
                except FileNotFoundError:
                    raise ValueError(f"No system prompt found for agent: {agent_id}")

            # Get model configuration from settings first, then fall back to config
            model = self.settings.get_agent_model(agent_id)
            agent_config = self.config.get('agents', {}).get(agent_id, {})
            max_tokens = agent_config.get('max_tokens', 8000)  # Must be > thinking_budget (5000)
            temperature = agent_config.get('temperature', 1.0)

            # Build thinking configuration
            thinking_config = {}
            if enable_thinking and 'sonnet-4' in model.lower():
                thinking_config = {
                    'type': 'enabled',
                    'budget_tokens': thinking_budget
                }

            # Get tool schemas if enabled
            tools = None
            if tools_enabled:
                tools = web_tools.get_web_tools_schema()

            # Tool use loop - keep calling until we get a final response
            all_thinking_text = ""
            all_response_text = ""
            total_input_tokens = 0
            total_output_tokens = 0
            total_thinking_tokens = 0
            tool_use_count = 0
            max_tool_uses = web_config.get('max_urls_per_turn', 3)

            while True:
                thinking_text = ""
                response_text = ""
                tool_uses = []

                # Retry loop for transient network errors
                for retry_attempt in range(self.max_retries + 1):
                    try:
                        # Make streaming API call
                        with self.client.messages.stream(
                            model=model,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            system=system_prompt,
                            messages=messages,
                            tools=tools,
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

                            # Get final message with token usage and tool uses
                            final_message = stream.get_final_message()
                            if final_message:
                                if hasattr(final_message, 'usage'):
                                    total_input_tokens += final_message.usage.input_tokens
                                    total_output_tokens += final_message.usage.output_tokens

                                # Check for tool uses
                                for content_block in final_message.content:
                                    if content_block.type == 'tool_use':
                                        tool_uses.append(content_block)

                        # Streaming succeeded - break out of retry loop
                        break

                    except anthropic.APIError:
                        # API errors (rate limits, auth, etc.) are not retryable - re-raise immediately
                        raise

                    except Exception as e:
                        # Network/connection errors - retry if we have attempts left
                        if retry_attempt < self.max_retries:
                            delay = self.retry_base_delay * (2 ** retry_attempt)
                            error_preview = str(e)[:100]  # First 100 chars
                            print(f"⚠️  Network error (attempt {retry_attempt + 1}/{self.max_retries + 1}): {error_preview}")
                            print(f"   Retrying in {delay}s...")
                            time.sleep(delay)
                            # Reset partial state before retry
                            thinking_text = ""
                            response_text = ""
                            tool_uses = []
                        else:
                            # Final attempt failed - re-raise to outer handler
                            raise

                # Accumulate text from this turn
                all_thinking_text += thinking_text
                all_response_text += response_text

                # If no tool uses, we're done
                if not tool_uses:
                    break

                # Check tool use limit
                if tool_use_count >= max_tool_uses:
                    print(f"⚠️  Reached maximum tool uses per turn ({max_tool_uses})")
                    break

                # Execute tools and prepare next message
                tool_results = []
                for tool_use in tool_uses:
                    tool_use_count += 1
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    tool_id = tool_use.id

                    # Notify about tool use
                    yield ('tool_use', f"Fetching: {tool_input.get('url', 'unknown')}", {})

                    # Execute the tool
                    tool_result = web_tools.execute_tool(tool_name, tool_input, web_config)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result
                    })

                # Add assistant message with tool use
                messages.append({
                    "role": "assistant",
                    "content": final_message.content
                })

                # Add tool results as user message
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue loop to get agent's response after tool execution

            # Estimate thinking tokens from thinking text if not provided by API
            if all_thinking_text and total_thinking_tokens == 0:
                total_thinking_tokens = len(all_thinking_text) // 4

            # Yield final token info with enhanced metadata
            token_info = {
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'thinking_tokens': total_thinking_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'thinking_text': all_thinking_text,
                'response_text': all_response_text,
                # Add model configuration
                'model_name': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                # Add tool usage stats
                'tool_uses': tool_use_count
            }
            yield ('complete', '', token_info)

            # Log token usage if debug enabled
            if self.config.get('logging', {}).get('debug', False):
                print(f"[DEBUG] Agent {agent_id} tokens: "
                      f"in={total_input_tokens} out={total_output_tokens} tools={tool_use_count}")

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


class Agent:
    """
    Wrapper class for an individual agent that provides a simple interface
    for the coordinator to interact with.
    """

    def __init__(self, agent_id: str, agent_name: str, runner: AgentRunner):
        """
        Initialize an agent wrapper.

        Args:
            agent_id: The agent identifier (e.g., 'agent_a', 'agent_b')
            agent_name: The display name for the agent
            runner: The AgentRunner instance to use for API calls
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.runner = runner

    def send_message(self, context_messages: List[Message], message: str) -> Optional[str]:
        """
        Send a message to the agent and get a response.

        Args:
            context_messages: Previous conversation context
            message: The message to send

        Returns:
            The agent's response text, or None if failed
        """
        return self.runner.send_message_to_agent(self.agent_id, context_messages, message)

    def send_message_streaming(
        self,
        context_messages: List[Message],
        message: str,
        enable_thinking: bool = True,
        thinking_budget: int = 5000
    ):
        """
        Send a message to the agent with streaming response.

        Args:
            context_messages: Previous conversation context
            message: The message to send
            enable_thinking: Whether to show extended thinking
            thinking_budget: Maximum tokens for thinking

        Yields:
            Tuples of (content_type, chunk, token_info)
        """
        return self.runner.send_message_streaming(
            self.agent_id,
            context_messages,
            message,
            enable_thinking,
            thinking_budget
        )


class AgentPool:
    """
    Pool of agents for managing multiple agent instances.
    This is a higher-level interface for creating and managing agents.
    """

    def __init__(self):
        """Initialize the agent pool."""
        # Load config from config.yaml
        config_path = Path('config.yaml')
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            # Default minimal config
            self.config = {
                'agents': {},
                'logging': {'debug': False}
            }

        # Create a single AgentRunner instance
        self.runner = AgentRunner(self.config)

        # Track created agents
        self.agents: Dict[str, Agent] = {}

    def create_agent(self, agent_id: str, agent_name: str) -> Agent:
        """
        Create a new agent with the given ID and name.

        Args:
            agent_id: The agent identifier (e.g., 'agent_a', 'agent_b')
            agent_name: The display name for the agent

        Returns:
            An Agent instance
        """
        agent = Agent(agent_id, agent_name, self.runner)
        self.agents[agent_id] = agent
        return agent

    def validate_all_agents(self) -> bool:
        """
        Validate that all created agents are available and can respond.

        Returns:
            True if all agents are valid, False otherwise
        """
        if not self.agents:
            print("⚠️  No agents have been created yet")
            return False

        all_valid = True
        for agent_id, agent in self.agents.items():
            try:
                # Check if agent file exists (static or dynamic)
                static_path = Path('.claude') / 'agents' / f'{agent_id}.md'
                dynamic_path = Path('.claude') / 'agents' / 'dynamic' / f'{agent_id}.md'

                if not static_path.exists() and not dynamic_path.exists():
                    print(f"❌ Agent file not found at {static_path} or {dynamic_path}")
                    all_valid = False
                    continue

                # Check API key
                if not os.environ.get('ANTHROPIC_API_KEY'):
                    print("❌ ANTHROPIC_API_KEY environment variable not set")
                    all_valid = False
                    continue

                print(f"✅ Agent {agent.agent_name} (@{agent_id}) is ready")

            except Exception as e:
                print(f"❌ Agent {agent.agent_name} validation failed: {str(e)}")
                all_valid = False

        return all_valid
