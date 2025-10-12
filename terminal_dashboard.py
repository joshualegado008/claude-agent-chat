"""
Terminal Dashboard - Beautiful terminal-based metadata visualization
"""

import os
from typing import Dict, List, Optional
from colorama import Fore, Style, init
from cost_calculator import CostCalculator

# Initialize colorama
init(autoreset=True)


class TerminalDashboard:
    """Displays rich metadata in a beautiful terminal dashboard."""

    def __init__(self):
        self.width = 80

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def display_full_dashboard(
        self,
        metadata: Dict,
        conversation_title: str,
        total_turns: int,
        total_tokens: int,
        total_cost: Optional[float] = None
    ):
        """
        Display the complete metadata dashboard.

        Args:
            metadata: Rich metadata dict from MetadataExtractor
            conversation_title: Title of the conversation
            total_turns: Total number of turns
            total_tokens: Total tokens used
            total_cost: Optional total cost accumulated so far
        """
        self.clear_screen()

        # Header
        self._print_header("📊 CONVERSATION INTELLIGENCE DASHBOARD")

        # Conversation Overview
        overview_items = [
            f"Title: {Fore.CYAN}{conversation_title}{Style.RESET_ALL}",
            f"Turns: {Fore.GREEN}{total_turns}{Style.RESET_ALL}",
            f"Tokens: {Fore.YELLOW}{total_tokens:,}{Style.RESET_ALL}",
        ]

        # Add cost if available
        if total_cost is not None and total_cost > 0:
            cost_str = CostCalculator.format_cost(total_cost)
            overview_items.append(f"Cost: {Fore.GREEN}{cost_str}{Style.RESET_ALL}")

        overview_items.append(
            f"Stage: {Fore.MAGENTA}{metadata.get('conversation_stage', 'N/A').title()}{Style.RESET_ALL}"
        )

        self._print_section("🎯 Conversation Overview", overview_items)

        # Current Vibe
        vibe = metadata.get('current_vibe', 'N/A')
        self._print_box("💭 Current Vibe", vibe, Fore.CYAN)

        # Classification
        self._print_section("🏷️  Classification", [
            f"Content Type: {Fore.BLUE}{metadata.get('content_type', 'N/A').title()}{Style.RESET_ALL}",
            f"Technical Level: {Fore.GREEN}{metadata.get('technical_level', 'N/A').title()}{Style.RESET_ALL}",
            f"Sentiment: {self._get_sentiment_colored(metadata.get('sentiment', 'neutral'))}",
            f"Complexity: {self._get_complexity_bar(metadata.get('complexity_level', 5))}",
            f"Engagement: {self._get_engagement_indicator(metadata.get('engagement_quality', 'medium'))}"
        ])

        # Main Topics
        topics = metadata.get('main_topics', [])
        self._print_tag_section("🎓 Main Topics", topics, max_display=8)

        # Key Concepts
        concepts = metadata.get('key_concepts', [])
        if concepts:
            self._print_tag_section("💡 Key Concepts", concepts, max_display=8)

        # Emerging Themes
        themes = metadata.get('emerging_themes', [])
        if themes:
            self._print_tag_section("🌟 Emerging Themes", themes, max_display=6)

        # Named Entities
        entities = metadata.get('named_entities', {})
        if any(entities.values()):
            self._print_named_entities(entities)

        # Footer
        self._print_footer()

    def display_interrupt_menu(self) -> str:
        """
        Display the interrupt menu and get user choice.

        Returns:
            User's menu choice
        """
        print("\n" + "="*self.width)
        print(f"{Fore.YELLOW}⏸️  CONVERSATION PAUSED{Style.RESET_ALL}".center(self.width + 10))
        print("="*self.width)
        print()
        print("What would you like to do?\n")
        print(f"  {Fore.CYAN}1.{Style.RESET_ALL} 📊 View Stats & Context")
        print(f"  {Fore.CYAN}2.{Style.RESET_ALL} 💬 Say Something {Fore.YELLOW}(Coming Soon){Style.RESET_ALL}")
        print(f"  {Fore.CYAN}3.{Style.RESET_ALL} 💾 Save Snapshot")
        print(f"  {Fore.CYAN}4.{Style.RESET_ALL} ⏹️  Stop Conversation")
        print(f"  {Fore.CYAN}5.{Style.RESET_ALL} ▶️  Resume")
        print()

        choice = input(f"{Fore.GREEN}Enter choice (1-5):{Style.RESET_ALL} ").strip()
        return choice

    def display_compact_update(self, metadata: Dict, turn_number: int):
        """
        Display a compact metadata update (non-intrusive).

        Args:
            metadata: Current metadata
            turn_number: Current turn number
        """
        vibe = metadata.get('current_vibe', 'N/A')[:50]
        stage = metadata.get('conversation_stage', 'N/A')

        print(f"\n{Fore.BLUE}[Turn {turn_number}]{Style.RESET_ALL} "
              f"{Fore.YELLOW}Stage: {stage}{Style.RESET_ALL} • "
              f"💭 {vibe}...\n")

    def _print_header(self, title: str):
        """Print dashboard header."""
        print("\n" + "╔" + "═"*(self.width-2) + "╗")
        print("║" + title.center(self.width-2 + 10) + "║")
        print("╚" + "═"*(self.width-2) + "╝\n")

    def _print_section(self, title: str, items: List[str]):
        """Print a section with items."""
        print(f"\n{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        print("─"*self.width)
        for item in items:
            print(f"  {item}")
        print()

    def _print_box(self, title: str, content: str, color: str = Fore.WHITE):
        """Print content in a box."""
        print(f"\n{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        print("┌" + "─"*(self.width-2) + "┐")

        # Word wrap content
        words = content.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= self.width - 6:
                line += word + " "
            else:
                print(f"│ {color}{line.strip()}{Style.RESET_ALL}".ljust(self.width + 10) + "│")
                line = word + " "
        if line:
            print(f"│ {color}{line.strip()}{Style.RESET_ALL}".ljust(self.width + 10) + "│")

        print("└" + "─"*(self.width-2) + "┘\n")

    def _print_tag_section(self, title: str, tags: List[str], max_display: int = 10):
        """Print tags with overflow indicator."""
        print(f"\n{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        print("─"*self.width)

        if not tags:
            print(f"  {Fore.YELLOW}No items identified{Style.RESET_ALL}\n")
            return

        # Display tags
        displayed = tags[:max_display]
        overflow = len(tags) - max_display

        # Format as inline tags
        tag_str = "  "
        for tag in displayed:
            tag_display = f"{Fore.CYAN}{tag}{Style.RESET_ALL}"
            tag_str += tag_display + " • "

        # Remove trailing bullet
        tag_str = tag_str.rstrip(" • ")

        if overflow > 0:
            tag_str += f" {Fore.YELLOW}+{overflow} more{Style.RESET_ALL}"

        print(tag_str)
        print()

    def _print_named_entities(self, entities: Dict):
        """Print named entities section."""
        print(f"\n{Fore.WHITE}{Style.BRIGHT}🔍 Named Entities{Style.RESET_ALL}")
        print("─"*self.width)

        entity_types = {
            'people': ('👥', 'People'),
            'organizations': ('🏢', 'Organizations'),
            'locations': ('📍', 'Locations'),
            'technologies': ('💻', 'Technologies')
        }

        has_any = False
        for key, (emoji, label) in entity_types.items():
            items = entities.get(key, [])
            if items:
                has_any = True
                display_items = items[:5]
                overflow = len(items) - 5

                items_str = f"{emoji} {Fore.CYAN}{label}:{Style.RESET_ALL} "
                items_str += ", ".join(display_items)

                if overflow > 0:
                    items_str += f" {Fore.YELLOW}+{overflow} more{Style.RESET_ALL}"

                print(f"  {items_str}")

        if not has_any:
            print(f"  {Fore.YELLOW}No named entities identified{Style.RESET_ALL}")

        print()

    def _print_footer(self):
        """Print dashboard footer."""
        print("─"*self.width)
        print(f"{Fore.YELLOW}Press any key to return to conversation...{Style.RESET_ALL}")
        print("="*self.width + "\n")

    def _get_sentiment_colored(self, sentiment: str) -> str:
        """Get colored sentiment indicator."""
        colors = {
            'positive': Fore.GREEN,
            'negative': Fore.RED,
            'neutral': Fore.YELLOW,
            'mixed': Fore.CYAN,
            'critical': Fore.RED
        }
        color = colors.get(sentiment.lower(), Fore.WHITE)
        return f"{color}{sentiment.title()}{Style.RESET_ALL}"

    def _get_complexity_bar(self, level: int) -> str:
        """Get visual complexity bar."""
        level = max(1, min(10, level))  # Clamp to 1-10
        filled = "█" * level
        empty = "░" * (10 - level)

        if level <= 3:
            color = Fore.GREEN
        elif level <= 7:
            color = Fore.YELLOW
        else:
            color = Fore.RED

        return f"{color}{filled}{Fore.WHITE}{empty}{Style.RESET_ALL} ({level}/10)"

    def _get_engagement_indicator(self, quality: str) -> str:
        """Get visual engagement indicator."""
        indicators = {
            'high': f"{Fore.GREEN}🔥🔥🔥 High{Style.RESET_ALL}",
            'medium': f"{Fore.YELLOW}🔥🔥 Medium{Style.RESET_ALL}",
            'low': f"{Fore.RED}🔥 Low{Style.RESET_ALL}"
        }
        return indicators.get(quality.lower(), f"{Fore.WHITE}{quality}{Style.RESET_ALL}")

    def show_help_hint(self):
        """Show hint about interrupt feature."""
        print(f"\n{Fore.CYAN}💡 Tip: Press CTRL-C at any time to pause and view stats{Style.RESET_ALL}\n")
