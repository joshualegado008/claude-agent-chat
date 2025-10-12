"""
Display Formatter - Terminal output formatting for agent conversations

Features:
- Color-coded agent responses
- Progress indicators
- Token usage display with costs
- Context window visualization
- Clean, readable output
"""

import os
import sys
from typing import Dict, Optional
from datetime import datetime
from cost_calculator import CostCalculator

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

    def print_thinking_header(self, agent_name: str):
        """Print header for thinking section"""
        if self.use_colors:
            print(f"\n{Fore.YELLOW}{Style.DIM}💭 {agent_name} is thinking...{Style.RESET_ALL}")
        else:
            print(f"\n💭 {agent_name} is thinking...")
        print(f"{Fore.YELLOW}{Style.DIM}{'─' * 60}{Style.RESET_ALL}")

    def print_thinking_chunk(self, chunk: str):
        """Print a chunk of thinking content in real-time"""
        if self.use_colors:
            print(f"{Fore.YELLOW}{Style.DIM}{chunk}{Style.RESET_ALL}", end='', flush=True)
        else:
            print(chunk, end='', flush=True)

    def print_thinking_end(self):
        """Print separator at end of thinking"""
        if self.use_colors:
            print(f"\n{Fore.YELLOW}{Style.DIM}{'─' * 60}{Style.RESET_ALL}")
        else:
            print(f"\n{'─' * 60}")

    def print_response_header(self, agent_name: str, agent_id: str):
        """Print header for response section"""
        color = self.agent_colors.get(agent_id, Fore.WHITE)
        if self.use_colors:
            print(f"\n{color}{Style.BRIGHT}💬 {agent_name} responds:{Style.RESET_ALL}")
        else:
            print(f"\n💬 {agent_name} responds:")
        print(f"{color}{'─' * 60}{Style.RESET_ALL}")

    def print_streaming_chunk(self, chunk: str, agent_id: str):
        """Print a chunk of response content in real-time"""
        color = self.agent_colors.get(agent_id, Fore.WHITE)
        if self.use_colors:
            print(f"{color}{chunk}{Style.RESET_ALL}", end='', flush=True)
        else:
            print(chunk, end='', flush=True)

    def print_response_end(self):
        """Print newline at end of response"""
        print()  # Just a newline to finish the response

    # ============================================================================
    # Static methods for coordinator_with_memory.py
    # ============================================================================

    @staticmethod
    def print_header():
        """Print the application header"""
        header = """
╔══════════════════════════════════════════════════════════════╗
║         🤖 Agent-to-Agent Conversation Coordinator 🤖        ║
║                  with Persistent Memory                      ║
╚══════════════════════════════════════════════════════════════╝
"""
        if COLORS_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}{header}{Style.RESET_ALL}")
        else:
            print(header)

    @staticmethod
    def print_success(message: str):
        """Print success message"""
        if COLORS_AVAILABLE:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"✅ {message}")

    @staticmethod
    def print_token_stats(turn_tokens: int, total_tokens: int, model_name: str = None,
                         input_tokens: int = 0, output_tokens: int = 0,
                         turn_cost: float = 0.0, total_cost: float = 0.0):
        """
        Print token usage statistics with cost information.

        Args:
            turn_tokens: Total tokens for this turn
            total_tokens: Total tokens for session
            model_name: Model name for cost calculation
            input_tokens: Input tokens for this turn
            output_tokens: Output tokens for this turn
            turn_cost: Pre-calculated turn cost (optional)
            total_cost: Pre-calculated total cost (optional)
        """
        if turn_tokens > 0:
            color = Fore.GREEN if total_tokens < 50000 else (
                Fore.YELLOW if total_tokens < 100000 else Fore.RED
            )

            # Calculate costs if not provided and model name is given
            if turn_cost == 0.0 and model_name and input_tokens > 0:
                cost_info = CostCalculator.calculate_cost(model_name, input_tokens, output_tokens)
                turn_cost = cost_info['total_cost']

            # Format cost strings
            turn_cost_str = CostCalculator.format_cost(turn_cost) if turn_cost > 0 else ""
            total_cost_str = CostCalculator.format_cost(total_cost) if total_cost > 0 else ""

            # Build display string
            if turn_cost > 0 or total_cost > 0:
                if COLORS_AVAILABLE:
                    print(f"\n{Style.DIM}💰 Tokens: {color}+{turn_tokens:,}{Style.RESET_ALL}{Style.DIM} ({turn_cost_str}) | Session: {color}{total_tokens:,}{Style.RESET_ALL}{Style.DIM} ({total_cost_str}){Style.RESET_ALL}")
                else:
                    print(f"\n💰 Tokens: +{turn_tokens:,} ({turn_cost_str}) | Session: {total_tokens:,} ({total_cost_str})")
            else:
                # Fallback to original format if no cost info
                if COLORS_AVAILABLE:
                    print(f"\n{Style.DIM}💰 Tokens: {color}+{turn_tokens:,}{Style.RESET_ALL}{Style.DIM} (Session total: {color}{total_tokens:,}{Style.RESET_ALL}{Style.DIM}){Style.RESET_ALL}")
                else:
                    print(f"\n💰 Tokens: +{turn_tokens:,} (Session total: {total_tokens:,})")

    @staticmethod
    def print_technical_stats(
        turn_tokens: int,
        total_tokens: int,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        thinking_tokens: int,
        turn_cost: float,
        total_cost: float,
        context_stats: dict = None,
        session_stats: dict = None,
        model_config: dict = None
    ):
        """
        Print comprehensive technical stats for system engineers.

        Args:
            turn_tokens: Total tokens for this turn
            total_tokens: Total tokens for session
            model_name: Model being used
            input_tokens: Input tokens (context + prompt)
            output_tokens: Output tokens (response)
            thinking_tokens: Extended thinking tokens
            turn_cost: Cost for this turn
            total_cost: Total session cost
            context_stats: Dict with context window info
            session_stats: Dict with session analytics
            model_config: Dict with model configuration
        """
        # Format costs
        turn_cost_str = CostCalculator.format_cost(turn_cost)
        total_cost_str = CostCalculator.format_cost(total_cost)

        # Get context stats
        ctx_total_exchanges = context_stats.get('total_exchanges', 0) if context_stats else 0
        ctx_window_size = context_stats.get('window_size', 0) if context_stats else 0
        ctx_chars = context_stats.get('context_chars', 0) if context_stats else 0
        ctx_tokens_estimate = context_stats.get('context_tokens_estimate', 0) if context_stats else 0
        ctx_referenced_turns = context_stats.get('referenced_turns', []) if context_stats else []

        # Get session stats
        current_turn = session_stats.get('current_turn', 0) if session_stats else 0
        max_turns = session_stats.get('max_turns', 0) if session_stats else 0
        avg_tokens_per_turn = session_stats.get('avg_tokens_per_turn', 0) if session_stats else 0
        projected_total = session_stats.get('projected_total_tokens', 0) if session_stats else 0
        projected_cost = session_stats.get('projected_total_cost', 0) if session_stats else 0

        # Get model config
        temperature = model_config.get('temperature', 1.0) if model_config else 1.0
        max_tokens = model_config.get('max_tokens', 0) if model_config else 0

        # Calculate prompt-only tokens (input - context)
        prompt_tokens = input_tokens - ctx_tokens_estimate if ctx_tokens_estimate > 0 else input_tokens

        # Color coding based on token usage
        if COLORS_AVAILABLE:
            token_color = Fore.GREEN if total_tokens < 50000 else (
                Fore.YELLOW if total_tokens < 100000 else Fore.RED
            )
        else:
            token_color = ""

        # Build the geeky stats display
        print(f"\n┌─ 🔧 TECHNICAL STATS {'─' * 37}┐")

        # Model info line
        model_display = model_name[:35] if len(model_name) > 35 else model_name
        if COLORS_AVAILABLE:
            print(f"│ {Fore.CYAN}Model:{Style.RESET_ALL} {model_display} │ {Fore.CYAN}Temp:{Style.RESET_ALL} {temperature} │ {Fore.CYAN}Max:{Style.RESET_ALL} {max_tokens}")
        else:
            print(f"│ Model: {model_display} │ Temp: {temperature} │ Max: {max_tokens}")

        print(f"├{'─' * 59}┤")

        # Token breakdown section
        if COLORS_AVAILABLE:
            print(f"│ {Fore.YELLOW}{Style.BRIGHT}📊 Tokens (This Turn){Style.RESET_ALL}{' ' * 37}│")
        else:
            print(f"│ 📊 Tokens (This Turn){' ' * 37}│")

        # Input tokens breakdown
        input_cost_str = CostCalculator.format_cost(turn_cost * (input_tokens / turn_tokens)) if turn_tokens > 0 else "$0.00"
        if ctx_tokens_estimate > 0:
            if COLORS_AVAILABLE:
                print(f"│   {Fore.CYAN}Input:{Style.RESET_ALL}    {input_tokens:>5,} ({input_cost_str}) ← {ctx_tokens_estimate:>4,} context + {prompt_tokens:>3,} prompt{' ' * (15 - len(str(prompt_tokens)))}│")
            else:
                print(f"│   Input:    {input_tokens:>5,} ({input_cost_str}) ← {ctx_tokens_estimate:>4,} context + {prompt_tokens:>3,} prompt│")
        else:
            if COLORS_AVAILABLE:
                print(f"│   {Fore.CYAN}Input:{Style.RESET_ALL}    {input_tokens:>5,} ({input_cost_str}){' ' * 31}│")
            else:
                print(f"│   Input:    {input_tokens:>5,} ({input_cost_str})│")

        # Output tokens
        output_cost_str = CostCalculator.format_cost(turn_cost * (output_tokens / turn_tokens)) if turn_tokens > 0 else "$0.00"
        if COLORS_AVAILABLE:
            print(f"│   {Fore.GREEN}Output:{Style.RESET_ALL}   {output_tokens:>5,} ({output_cost_str}) → response{' ' * 24}│")
        else:
            print(f"│   Output:   {output_tokens:>5,} ({output_cost_str}) → response│")

        # Thinking tokens (if any)
        if thinking_tokens > 0:
            thinking_cost_str = CostCalculator.format_cost(turn_cost * (thinking_tokens / turn_tokens)) if turn_tokens > 0 else "$0.00"
            if COLORS_AVAILABLE:
                print(f"│   {Fore.YELLOW}Thinking:{Style.RESET_ALL} {thinking_tokens:>5,} ({thinking_cost_str}) 💭 extended reasoning{' ' * 13}│")
            else:
                print(f"│   Thinking: {thinking_tokens:>5,} ({thinking_cost_str}) 💭 extended reasoning│")

        # Total for turn
        if COLORS_AVAILABLE:
            print(f"│   {Style.BRIGHT}Total:{Style.RESET_ALL}    {token_color}{turn_tokens:>5,}{Style.RESET_ALL} ({turn_cost_str}){' ' * 31}│")
        else:
            print(f"│   Total:    {turn_tokens:>5,} ({turn_cost_str})│")

        # Context window section (if context stats provided)
        if context_stats and ctx_total_exchanges > 0:
            print(f"├{'─' * 59}┤")
            if COLORS_AVAILABLE:
                print(f"│ {Fore.MAGENTA}{Style.BRIGHT}🪟 Context Window{Style.RESET_ALL}{' ' * 42}│")
            else:
                print(f"│ 🪟 Context Window{' ' * 42}│")

            print(f"│   Total exchanges:      {ctx_total_exchanges:>3} turns{' ' * 30}│")
            print(f"│   Window size:          {ctx_window_size:>3} turns (last {ctx_window_size} used){' ' * (16 - len(str(ctx_window_size)))}│")
            print(f"│   Context chars:      ~{ctx_chars:>5,} chars → ~{ctx_tokens_estimate:>4,} tokens{' ' * (14 - len(f'{ctx_tokens_estimate:,}'))}│")

            if ctx_referenced_turns:
                turns_str = str(ctx_referenced_turns)[1:-1]  # Remove brackets
                if len(turns_str) > 40:
                    turns_str = turns_str[:37] + "..."
                print(f"│   Referenced turns:    [{turns_str}]{' ' * (34 - len(turns_str))}│")

        # Session stats section
        if session_stats and current_turn > 0:
            print(f"├{'─' * 59}┤")
            if COLORS_AVAILABLE:
                print(f"│ {Fore.BLUE}{Style.BRIGHT}📈 Session Stats{Style.RESET_ALL}{' ' * 42}│")
            else:
                print(f"│ 📈 Session Stats{' ' * 42}│")

            print(f"│   Current turn:     {current_turn:>3} / {max_turns:<3}{' ' * 36}│")
            print(f"│   Total tokens:  {total_tokens:>6,} ({total_cost_str}){' ' * (31 - len(f'{total_tokens:,}') - len(total_cost_str))}│")
            print(f"│   Avg/turn:       {avg_tokens_per_turn:>5,} tokens{' ' * (33 - len(f'{avg_tokens_per_turn:,}'))}│")

            if max_turns > current_turn:
                proj_cost_str = CostCalculator.format_cost(projected_cost)
                print(f"│   Est. at max:  ~{projected_total:>6,} tokens ({proj_cost_str}){' ' * (22 - len(f'{projected_total:,}') - len(proj_cost_str))}│")

        print(f"└{'─' * 59}┘")

    @staticmethod
    def print_streaming_agent_response(agent, message: str, show_thinking: bool = True):
        """
        Print a streaming agent response.

        Args:
            agent: Agent object with agent_name and send_message_streaming method
            message: Message to send to the agent
            show_thinking: Whether to show thinking content

        Returns:
            Tuple of (response_text, token_info_dict) where token_info_dict contains:
            - 'total_tokens': int
            - 'input_tokens': int
            - 'output_tokens': int
            - 'model': str (if available)
        """
        response_text = ""
        thinking_text = ""
        has_thinking = False
        input_tokens = 0
        output_tokens = 0

        try:
            # Get streaming response from agent
            stream = agent.send_message_streaming(
                context_messages=[],
                message=message,
                enable_thinking=show_thinking,
                thinking_budget=5000
            )

            for content_type, chunk, info in stream:
                if content_type == 'thinking_start':
                    # Start thinking display
                    if show_thinking:
                        has_thinking = True
                        if COLORS_AVAILABLE:
                            print(f"\n{Fore.YELLOW}{Style.DIM}💭 {agent.agent_name} is thinking...{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}{Style.DIM}{'─' * 60}{Style.RESET_ALL}")
                        else:
                            print(f"\n💭 {agent.agent_name} is thinking...")
                            print('─' * 60)

                elif content_type == 'thinking':
                    # Display thinking chunks in real-time
                    if show_thinking:
                        thinking_text += chunk
                        if COLORS_AVAILABLE:
                            print(f"{Fore.YELLOW}{Style.DIM}{chunk}{Style.RESET_ALL}", end='', flush=True)
                        else:
                            print(chunk, end='', flush=True)

                elif content_type == 'text':
                    # First text chunk - show response header
                    if not response_text:
                        if has_thinking and show_thinking:
                            if COLORS_AVAILABLE:
                                print(f"\n{Fore.YELLOW}{Style.DIM}{'─' * 60}{Style.RESET_ALL}")
                            else:
                                print(f"\n{'─' * 60}")

                        if COLORS_AVAILABLE:
                            print(f"\n{Fore.CYAN}{Style.BRIGHT}💬 {agent.agent_name} responds:{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}\n")
                        else:
                            print(f"\n💬 {agent.agent_name} responds:")
                            print('─' * 60 + '\n')

                    # Display response chunks in real-time
                    response_text += chunk
                    if COLORS_AVAILABLE:
                        print(f"{Fore.CYAN}{chunk}{Style.RESET_ALL}", end='', flush=True)
                    else:
                        print(chunk, end='', flush=True)

                elif content_type == 'complete':
                    # Stream complete
                    if response_text:
                        print()  # Newline at end
                    input_tokens = info.get('input_tokens', 0)
                    output_tokens = info.get('output_tokens', 0)

                elif content_type == 'error':
                    if COLORS_AVAILABLE:
                        print(f"\n{Fore.RED}{Style.BRIGHT}❌ Error:{Style.RESET_ALL} {chunk}")
                    else:
                        print(f"\n❌ Error: {chunk}")
                    break

        except Exception as e:
            if COLORS_AVAILABLE:
                print(f"\n{Fore.RED}{Style.BRIGHT}❌ Error during streaming:{Style.RESET_ALL} {e}")
            else:
                print(f"\n❌ Error during streaming: {e}")

        total_tokens = input_tokens + output_tokens

        # Get model info from agent if available
        model_name = None
        if hasattr(agent, 'runner') and hasattr(agent.runner, 'config'):
            agent_config = agent.runner.config.get('agents', {}).get(agent.agent_id, {})
            model_name = agent_config.get('model')

        token_info = {
            'total_tokens': total_tokens,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'model': model_name
        }

        return response_text, token_info

    @staticmethod
    def print_turn_header(turn_number: int, agent_name: str):
        """Print header for a conversation turn"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        print("\n" + "─"*60)
        if COLORS_AVAILABLE:
            print(f"{Fore.CYAN}{Style.BRIGHT}Turn {turn_number}: {agent_name}{Style.RESET_ALL} [{timestamp}]")
        else:
            print(f"Turn {turn_number}: {agent_name} [{timestamp}]")
        print("─"*60)

    @staticmethod
    def print_info(message: str):
        """Print info message (static version)"""
        if COLORS_AVAILABLE:
            print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")
        else:
            print(f"ℹ️  {message}")

    @staticmethod
    def print_error(message: str):
        """Print error message (static version)"""
        if COLORS_AVAILABLE:
            print(f"\n{Fore.RED}{Style.BRIGHT}❌ Error:{Style.RESET_ALL} {message}")
        else:
            print(f"\n❌ Error: {message}")

    @staticmethod
    def print_warning(message: str):
        """Print warning message (static version)"""
        if COLORS_AVAILABLE:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  Warning:{Style.RESET_ALL} {message}")
        else:
            print(f"\n⚠️  Warning: {message}")
