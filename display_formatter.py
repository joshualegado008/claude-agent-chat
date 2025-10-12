"""
Display Formatter - Terminal output formatting for agent conversations

Features:
- Color-coded agent responses
- Progress indicators
- Token usage display
- Context window visualization
- Clean, readable output
"""

import os
import sys
from typing import Dict, Optional
from datetime import datetime

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Fallback if colorama not installed
    class Fore:
        CYAN = YELLOW = GREEN = RED = MAGENTA = BLUE = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""


class DisplayFormatter:
    """Handles formatted terminal output for agent conversations"""

    def __init__(self, config: Dict):
        self.config = config
        self.display_config = config.get('display', {})
        self.agents_config = config.get('agents', {})

        self.use_colors = self.display_config.get('use_colors', True) and COLORS_AVAILABLE
        self.show_tokens = self.display_config.get('show_tokens', True)
        self.show_timestamps = self.display_config.get('show_timestamps', True)
        self.clear_screen = self.display_config.get('clear_screen', False)

        # Agent color mapping
        self.agent_colors = {}
        for agent_id, agent_info in self.agents_config.items():
            color_name = agent_info.get('color', 'white').upper()
            self.agent_colors[agent_id] = getattr(Fore, color_name, Fore.WHITE)

    def clear(self):
        """Clear the terminal screen"""
        if self.clear_screen:
            os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        """Print the welcome banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║         🤖 Agent-to-Agent Conversation Coordinator 🤖        ║
║                                                              ║
║  Two Claude agents engaging in intelligent discussion        ║
╚══════════════════════════════════════════════════════════════╝
"""
        if self.use_colors:
            print(f"{Fore.CYAN}{Style.BRIGHT}{banner}{Style.RESET_ALL}")
        else:
            print(banner)

    def print_agent_info(self):
        """Print information about the agents"""
        print("\n" + "="*60)
        print("Agents Participating:")
        print("="*60)

        for agent_id, agent_info in self.agents_config.items():
            name = agent_info.get('name', agent_id)
            color = self.agent_colors.get(agent_id, Fore.WHITE)

            if self.use_colors:
                print(f"  {color}{Style.BRIGHT}● {name}{Style.RESET_ALL} (@{agent_id})")
            else:
                print(f"  ● {name} (@{agent_id})")

        print("="*60 + "\n")

    def print_conversation_start(self, initial_prompt: str, max_turns: int):
        """Print conversation start information"""
        print("\n" + "─"*60)
        if self.use_colors:
            print(f"{Fore.GREEN}{Style.BRIGHT}Starting Conversation{Style.RESET_ALL}")
        else:
            print("Starting Conversation")

        print("─"*60)
        print(f"\n{Style.BRIGHT}Initial Prompt:{Style.RESET_ALL}")
        print(f"  {initial_prompt}")
        print(f"\n{Style.BRIGHT}Configuration:{Style.RESET_ALL}")
        print(f"  Max turns: {max_turns}")
        print("─"*60 + "\n")

    def print_turn_header(self, turn_number: int, agent_id: str, agent_name: str):
        """Print header for a conversation turn"""
        color = self.agent_colors.get(agent_id, Fore.WHITE)

        timestamp = datetime.now().strftime("%H:%M:%S") if self.show_timestamps else ""
        timestamp_str = f" [{timestamp}]" if timestamp else ""

        print("\n" + "─"*60)
        if self.use_colors:
            print(f"{color}{Style.BRIGHT}Turn {turn_number}: {agent_name}{Style.RESET_ALL}{timestamp_str}")
        else:
            print(f"Turn {turn_number}: {agent_name}{timestamp_str}")
        print("─"*60)

    def print_message(self, message: str, agent_id: Optional[str] = None, indent: int = 0):
        """Print a message with optional color coding"""
        color = self.agent_colors.get(agent_id, Fore.WHITE) if agent_id else ""
        indent_str = " " * indent

        # Split message into lines and apply indent
        lines = message.split('\n')
        for line in lines:
            if self.use_colors and color:
                print(f"{indent_str}{color}{line}{Style.RESET_ALL}")
            else:
                print(f"{indent_str}{line}")

    def print_context_summary(self, num_messages: int, total_tokens: int):
        """Print summary of context being provided"""
        if not self.show_tokens:
            return

        print(f"\n{Style.DIM}  [Context: {num_messages} messages, ~{total_tokens} tokens]{Style.RESET_ALL}")

    def print_token_usage(self, turn_tokens: int, total_tokens: int):
        """Print token usage information"""
        if not self.show_tokens:
            return

        color = Fore.GREEN if total_tokens < 5000 else (Fore.YELLOW if total_tokens < 10000 else Fore.RED)

        if self.use_colors:
            print(f"\n{Style.DIM}  Tokens: {color}+{turn_tokens}{Style.RESET_ALL}{Style.DIM} (Total: {color}{total_tokens}{Style.RESET_ALL}{Style.DIM}){Style.RESET_ALL}")
        else:
            print(f"\n  Tokens: +{turn_tokens} (Total: {total_tokens})")

    def print_checkpoint(self, turn_number: int):
        """Print checkpoint indicator"""
        if self.use_colors:
            print(f"\n{Fore.MAGENTA}{Style.BRIGHT}  📌 Checkpoint created at turn {turn_number}{Style.RESET_ALL}")
        else:
            print(f"\n  📌 Checkpoint created at turn {turn_number}")

    def print_error(self, message: str):
        """Print error message"""
        if self.use_colors:
            print(f"\n{Fore.RED}{Style.BRIGHT}❌ Error:{Style.RESET_ALL} {message}")
        else:
            print(f"\n❌ Error: {message}")

    def print_warning(self, message: str):
        """Print warning message"""
        if self.use_colors:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  Warning:{Style.RESET_ALL} {message}")
        else:
            print(f"\n⚠️  Warning: {message}")

    def print_info(self, message: str):
        """Print info message"""
        if self.use_colors:
            print(f"\n{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")
        else:
            print(f"\nℹ️  {message}")

    def print_progress(self, current: int, total: int, message: str = ""):
        """Print progress indicator"""
        percentage = int((current / total) * 100) if total > 0 else 0
        bar_length = 30
        filled = int((bar_length * current) / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        status = f" - {message}" if message else ""

        if self.use_colors:
            print(f"\r{Fore.CYAN}Progress: [{bar}] {percentage}%{Style.RESET_ALL}{status}", end='', flush=True)
        else:
            print(f"\rProgress: [{bar}] {percentage}%{status}", end='', flush=True)

    def print_conversation_end(self, total_turns: int, total_tokens: int):
        """Print conversation end summary"""
        print("\n\n" + "="*60)
        if self.use_colors:
            print(f"{Fore.GREEN}{Style.BRIGHT}Conversation Complete{Style.RESET_ALL}")
        else:
            print("Conversation Complete")

        print("="*60)
        print(f"\nTotal turns: {total_turns}")
        if self.show_tokens:
            print(f"Total tokens: ~{total_tokens}")
        print("\n" + "="*60 + "\n")

    def print_saving_logs(self, json_path: str, md_path: Optional[str] = None):
        """Print log saving information"""
        self.print_info(f"Saving conversation log to: {json_path}")
        if md_path:
            self.print_info(f"Saving transcript to: {md_path}")

    def input_prompt(self, message: str) -> str:
        """Display a prompt and get user input"""
        if self.use_colors:
            return input(f"{Fore.YELLOW}{Style.BRIGHT}{message}{Style.RESET_ALL} ")
        else:
            return input(f"{message} ")

    def confirm(self, message: str, default: bool = True) -> bool:
        """Display a yes/no confirmation prompt"""
        options = "[Y/n]" if default else "[y/N]"
        response = self.input_prompt(f"{message} {options}:").lower().strip()

        if not response:
            return default

        return response in ['y', 'yes']
