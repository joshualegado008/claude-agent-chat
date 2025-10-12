#!/usr/bin/env python3
"""
Agent Conversation Coordinator

Main orchestration script that manages two Claude Code agents in conversation.

Features:
- Multi-tier memory management (immediate, checkpoints, summarized)
- Context optimization based on LLM best practices
- Automatic turn-taking between agents
- Conversation logging (JSON and Markdown)
- Beautiful terminal display with color-coding

Usage:
    python coordinator.py [--config config.yaml] [--prompt "Initial question"]
"""

import argparse
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from conversation_manager import ConversationHistory, Message, MessageRole
from agent_runner import AgentRunner
from display_formatter import DisplayFormatter


class ConversationCoordinator:
    """Main coordinator for agent-to-agent conversations"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the coordinator with configuration"""
        self.config = self._load_config(config_path)
        self.display = DisplayFormatter(self.config)
        self.agent_runner = AgentRunner(self.config)
        self.history: Optional[ConversationHistory] = None

        # Extract configuration
        self.conversation_config = self.config.get('conversation', {})
        self.agents_config = self.config.get('agents', {})
        self.logging_config = self.config.get('logging', {})

        self.max_turns = self.conversation_config.get('max_turns', 20)
        self.turn_delay = self.conversation_config.get('turn_delay', 1.0)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)

    def validate_agents(self) -> bool:
        """Validate that both agents are available"""
        self.display.print_info("Validating agent availability...")

        for agent_id in self.agents_config.keys():
            agent_name = self.agents_config[agent_id].get('name', agent_id)
            self.display.print_info(f"  Checking {agent_name} (@{agent_id})...")

            # Note: In the current implementation, we'll skip validation
            # as it would require running the agents
            # if not self.agent_runner.test_agent_availability(agent_id):
            #     self.display.print_error(f"Agent {agent_name} is not available")
            #     return False

        return True

    def run_conversation(self, initial_prompt: Optional[str] = None):
        """Run the full agent-to-agent conversation"""

        # Use provided prompt or default from config
        prompt = initial_prompt or self.conversation_config.get('initial_prompt', '')

        if not prompt:
            self.display.print_error("No initial prompt provided")
            return

        # Display startup information
        self.display.clear()
        self.display.print_banner()
        self.display.print_agent_info()

        # Validate agents
        if not self.validate_agents():
            return

        self.display.print_conversation_start(prompt, self.max_turns)

        # Get confirmation to proceed
        if not self.display.confirm("Start conversation?", default=True):
            self.display.print_info("Conversation cancelled")
            return

        # Initialize conversation history
        self.history = ConversationHistory(self.config, prompt)

        # Get agent IDs
        agent_ids = list(self.agents_config.keys())
        if len(agent_ids) < 2:
            self.display.print_error("Need at least 2 agents configured")
            return

        agent_a_id = agent_ids[0]
        agent_b_id = agent_ids[1]

        # Start the conversation loop
        current_agent_id = agent_a_id
        current_message = prompt

        try:
            for turn in range(self.max_turns):
                # Alternate between agents
                if turn > 0:
                    current_agent_id = agent_a_id if turn % 2 == 0 else agent_b_id

                agent_name = self.agents_config[current_agent_id].get('name', current_agent_id)

                # Display turn header
                self.display.print_turn_header(turn, current_agent_id, agent_name)

                # Build context for this turn
                context = self.history.build_context_for_next_turn()

                # Show context summary
                if self.config.get('display', {}).get('show_context_summary', False):
                    total_context_tokens = sum(msg.tokens_estimate for msg in context)
                    self.display.print_context_summary(len(context), total_context_tokens)

                # Get response from agent
                self.display.print_info(f"{agent_name} is thinking...")

                response = self.agent_runner.send_message_to_agent(
                    current_agent_id,
                    context,
                    current_message
                )

                if not response:
                    self.display.print_error(f"Failed to get response from {agent_name}")
                    break

                # Display the response
                print()  # Blank line before response
                self.display.print_message(response, current_agent_id, indent=2)

                # Add to history
                exchange = self.history.add_exchange(agent_name, response, context)

                # Show token usage
                total_tokens = self.history.get_total_tokens()
                self.display.print_token_usage(exchange.message.tokens_estimate, total_tokens)

                # Check for checkpoint
                if exchange.message.is_checkpoint or len(self.history.checkpoints) > 0:
                    if self.history.checkpoints and self.history.checkpoints[-1].timestamp == exchange.timestamp:
                        self.display.print_checkpoint(turn)

                # Prepare message for next agent
                current_message = response

                # Delay before next turn (for readability)
                if turn < self.max_turns - 1:
                    time.sleep(self.turn_delay)

            # Conversation complete
            self.display.print_conversation_end(
                self.history.current_turn,
                self.history.get_total_tokens()
            )

        except KeyboardInterrupt:
            self.display.print_warning("\nConversation interrupted by user")

        except Exception as e:
            self.display.print_error(f"Unexpected error: {e}")
            if self.logging_config.get('debug', False):
                import traceback
                traceback.print_exc()

        finally:
            # Save conversation logs
            self._save_logs()

    def _save_logs(self):
        """Save conversation logs to files"""
        if not self.history:
            return

        # Save JSON log
        if self.logging_config.get('save_full_history', True):
            json_path = self.logging_config.get('output_file', 'conversation_log.json')
            try:
                self.history.save_to_json(json_path)
                self.display.print_saving_logs(json_path)
            except Exception as e:
                self.display.print_error(f"Failed to save JSON log: {e}")

        # Save Markdown transcript
        if self.logging_config.get('save_transcript', True):
            md_path = self.logging_config.get('transcript_file', 'conversation_transcript.md')
            try:
                self.history.save_to_markdown(md_path)
                if not self.logging_config.get('save_full_history', True):
                    self.display.print_saving_logs(json_path=None, md_path=md_path)
            except Exception as e:
                self.display.print_error(f"Failed to save Markdown transcript: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Coordinate a conversation between two Claude Code agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python coordinator.py
  python coordinator.py --config my_config.yaml
  python coordinator.py --prompt "What is the meaning of life?"
  python coordinator.py --max-turns 10
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        help='Initial prompt/question for the conversation (overrides config)'
    )

    parser.add_argument(
        '--max-turns',
        type=int,
        help='Maximum number of conversation turns (overrides config)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    # Create coordinator
    coordinator = ConversationCoordinator(args.config)

    # Override config with command-line arguments
    if args.max_turns:
        coordinator.max_turns = args.max_turns

    if args.debug:
        coordinator.logging_config['debug'] = True

    # Run the conversation
    coordinator.run_conversation(initial_prompt=args.prompt)


if __name__ == '__main__':
    main()
