"""
Settings Manager - Manage user configuration for API keys and model selection

Stores settings in settings.json and provides a user-friendly interface
for configuration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from cost_calculator import CostCalculator


class SettingsManager:
    """Manage application settings including API keys and model selection."""

    DEFAULT_SETTINGS = {
        'anthropic_api_key': '',
        'openai_api_key': '',
        'agent_models': {
            'agent_a': 'claude-sonnet-4-5-20250929',
            'agent_b': 'claude-sonnet-4-5-20250929'
        },
        'embedding_model': 'text-embedding-3-small',
        'use_env_keys': True,  # Whether to prefer environment variables over stored keys
        'display_colors': {
            'thinking': 'LIGHTYELLOW_EX',
            'agents': {
                'agent_a': 'CYAN',
                'agent_b': 'YELLOW'
            }
        }
    }

    def __init__(self, settings_file: str = 'settings.json'):
        """
        Initialize settings manager.

        Args:
            settings_file: Path to settings file (default: settings.json)
        """
        self.settings_file = Path(settings_file)
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict:
        """Load settings from file or create default settings."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.DEFAULT_SETTINGS.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                print(f"Warning: Failed to load settings: {e}")
                print("Using default settings.")
                return self.DEFAULT_SETTINGS.copy()
        else:
            # First run - create default settings
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self) -> bool:
        """
        Save current settings to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_anthropic_api_key(self) -> Optional[str]:
        """
        Get Anthropic API key.

        Returns environment variable if use_env_keys is True and it exists,
        otherwise returns stored key.
        """
        if self.settings.get('use_env_keys', True):
            env_key = os.environ.get('ANTHROPIC_API_KEY')
            if env_key:
                return env_key

        return self.settings.get('anthropic_api_key') or None

    def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key.

        Returns environment variable if use_env_keys is True and it exists,
        otherwise returns stored key.
        """
        if self.settings.get('use_env_keys', True):
            env_key = os.environ.get('OPENAI_API_KEY')
            if env_key:
                return env_key

        return self.settings.get('openai_api_key') or None

    def set_anthropic_api_key(self, api_key: str):
        """Set Anthropic API key."""
        self.settings['anthropic_api_key'] = api_key
        self.save_settings()

    def set_openai_api_key(self, api_key: str):
        """Set OpenAI API key."""
        self.settings['openai_api_key'] = api_key
        self.save_settings()

    def get_agent_model(self, agent_id: str) -> str:
        """
        Get model for a specific agent.

        Args:
            agent_id: Agent identifier (e.g., 'agent_a', 'agent_b')

        Returns:
            Model name
        """
        return self.settings.get('agent_models', {}).get(
            agent_id,
            'claude-sonnet-4-5-20250929'
        )

    def set_agent_model(self, agent_id: str, model: str):
        """
        Set model for a specific agent.

        Args:
            agent_id: Agent identifier
            model: Model name
        """
        if 'agent_models' not in self.settings:
            self.settings['agent_models'] = {}

        self.settings['agent_models'][agent_id] = model
        self.save_settings()

    def get_embedding_model(self) -> str:
        """Get the embedding model to use."""
        return self.settings.get('embedding_model', 'text-embedding-3-small')

    def set_embedding_model(self, model: str):
        """Set the embedding model."""
        self.settings['embedding_model'] = model
        self.save_settings()

    def get_thinking_color(self) -> str:
        """Get the color for thinking text display."""
        return self.settings.get('display_colors', {}).get('thinking', 'LIGHTYELLOW_EX')

    def set_thinking_color(self, color: str):
        """
        Set the color for thinking text display.

        Args:
            color: Colorama color name (e.g., 'CYAN', 'LIGHTYELLOW_EX')
        """
        if not self._validate_color(color):
            raise ValueError(f"Invalid color name: {color}")

        if 'display_colors' not in self.settings:
            self.settings['display_colors'] = {}

        self.settings['display_colors']['thinking'] = color
        self.save_settings()

    def get_agent_color(self, agent_id: str) -> str:
        """
        Get the display color for a specific agent.

        Args:
            agent_id: Agent identifier (e.g., 'agent_a', 'agent_b')

        Returns:
            Colorama color name
        """
        default_colors = {'agent_a': 'CYAN', 'agent_b': 'YELLOW'}
        return self.settings.get('display_colors', {}).get('agents', {}).get(
            agent_id,
            default_colors.get(agent_id, 'WHITE')
        )

    def set_agent_color(self, agent_id: str, color: str):
        """
        Set the display color for a specific agent.

        Args:
            agent_id: Agent identifier (e.g., 'agent_a', 'agent_b')
            color: Colorama color name (e.g., 'CYAN', 'LIGHTYELLOW_EX')
        """
        if not self._validate_color(color):
            raise ValueError(f"Invalid color name: {color}")

        if 'display_colors' not in self.settings:
            self.settings['display_colors'] = {}
        if 'agents' not in self.settings['display_colors']:
            self.settings['display_colors']['agents'] = {}

        self.settings['display_colors']['agents'][agent_id] = color
        self.save_settings()

    def _validate_color(self, color: str) -> bool:
        """
        Validate that a color name exists in colorama.Fore.

        Args:
            color: Color name to validate

        Returns:
            True if valid, False otherwise
        """
        valid_colors = [
            'BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE',
            'LIGHTBLACK_EX', 'LIGHTRED_EX', 'LIGHTGREEN_EX', 'LIGHTYELLOW_EX',
            'LIGHTBLUE_EX', 'LIGHTMAGENTA_EX', 'LIGHTCYAN_EX', 'LIGHTWHITE_EX',
            'RESET'
        ]
        return color.upper() in valid_colors

    def get_available_colors(self) -> list:
        """
        Get list of available color names.

        Returns:
            List of tuples (color_name, display_name)
        """
        return [
            ('BLACK', 'Black'),
            ('RED', 'Red'),
            ('GREEN', 'Green'),
            ('YELLOW', 'Yellow'),
            ('BLUE', 'Blue'),
            ('MAGENTA', 'Magenta'),
            ('CYAN', 'Cyan'),
            ('WHITE', 'White'),
            ('LIGHTBLACK_EX', 'Light Black (Gray)'),
            ('LIGHTRED_EX', 'Light Red'),
            ('LIGHTGREEN_EX', 'Light Green'),
            ('LIGHTYELLOW_EX', 'Light Yellow'),
            ('LIGHTBLUE_EX', 'Light Blue'),
            ('LIGHTMAGENTA_EX', 'Light Magenta'),
            ('LIGHTCYAN_EX', 'Light Cyan'),
            ('LIGHTWHITE_EX', 'Light White (Bright)'),
        ]

    def set_use_env_keys(self, use_env: bool):
        """Set whether to prefer environment variables for API keys."""
        self.settings['use_env_keys'] = use_env
        self.save_settings()

    def get_use_env_keys(self) -> bool:
        """Check if environment variables are preferred for API keys."""
        return self.settings.get('use_env_keys', True)

    def validate_anthropic_key(self, api_key: Optional[str] = None) -> bool:
        """
        Validate Anthropic API key by attempting a test call.

        Args:
            api_key: Optional key to test. If None, uses current configured key.

        Returns:
            True if key is valid, False otherwise
        """
        if api_key is None:
            api_key = self.get_anthropic_api_key()

        if not api_key:
            return False

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            # Make a minimal test call
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            print(f"Anthropic API key validation failed: {e}")
            return False

    def validate_openai_key(self, api_key: Optional[str] = None) -> bool:
        """
        Validate OpenAI API key by attempting a test call.

        Args:
            api_key: Optional key to test. If None, uses current configured key.

        Returns:
            True if key is valid, False otherwise
        """
        if api_key is None:
            api_key = self.get_openai_api_key()

        if not api_key:
            return False

        try:
            import openai
            client = openai.OpenAI(api_key=api_key)

            # Make a minimal test call (list models is free)
            models = client.models.list()
            return True
        except Exception as e:
            print(f"OpenAI API key validation failed: {e}")
            return False

    def mask_key(self, key: str) -> str:
        """
        Mask an API key for display.

        Args:
            key: The API key to mask

        Returns:
            Masked version (e.g., "sk-ant-...abc123")
        """
        if not key or len(key) < 10:
            return "Not set"

        # Show first 7 chars and last 6 chars
        return f"{key[:7]}...{key[-6:]}"

    def display_current_settings(self):
        """Display current settings in a formatted way."""
        print("\n" + "="*60)
        print("Current Settings")
        print("="*60)

        # API Keys
        print("\n🔑 API Keys:")
        anthropic_key = self.get_anthropic_api_key()
        openai_key = self.get_openai_api_key()

        print(f"  Anthropic: {self.mask_key(anthropic_key) if anthropic_key else 'Not set'}")
        print(f"  OpenAI:    {self.mask_key(openai_key) if openai_key else 'Not set'}")

        if self.get_use_env_keys():
            print(f"  (Using environment variables when available)")

        # Agent Models
        print("\n🤖 Agent Models:")
        for agent_id in ['agent_a', 'agent_b']:
            model = self.get_agent_model(agent_id)
            display_name = CostCalculator._get_display_name(model)
            pricing = CostCalculator.get_model_pricing(model)

            print(f"  {agent_id}: {display_name}")
            print(f"           Model: {model}")
            print(f"           Pricing: ${pricing[0]:.2f}/${pricing[1]:.2f} per MTok (in/out)")

        # Embedding Model
        print(f"\n📊 Embedding Model: {self.get_embedding_model()}")

        print("="*60)

    def get_model_config_for_agent_runner(self) -> Dict:
        """
        Get model configuration in format expected by AgentRunner.

        Returns:
            Dictionary with agent configurations
        """
        return {
            'agents': {
                'agent_a': {
                    'model': self.get_agent_model('agent_a'),
                    'name': 'Nova',
                    'id': 'agent_a'
                },
                'agent_b': {
                    'model': self.get_agent_model('agent_b'),
                    'name': 'Atlas',
                    'id': 'agent_b'
                }
            }
        }

    def interactive_setup(self):
        """Run interactive setup wizard for first-time configuration."""
        print("\n" + "="*60)
        print("⚙️  Settings Configuration Wizard")
        print("="*60)

        print("\nThis wizard will help you configure API keys and model preferences.")
        print("Press Enter to skip any step and keep current value.\n")

        # Anthropic API Key
        print("\n1️⃣  Anthropic API Key (required for agents)")
        print("   Get your key from: https://console.anthropic.com/")
        current = self.get_anthropic_api_key()
        if current:
            print(f"   Current: {self.mask_key(current)}")

        new_key = input("   Enter new key (or press Enter to keep current): ").strip()
        if new_key:
            print("   Testing key...")
            if self.validate_anthropic_key(new_key):
                self.set_anthropic_api_key(new_key)
                print("   ✅ Key validated and saved!")
            else:
                print("   ❌ Key validation failed. Not saved.")

        # OpenAI API Key
        print("\n2️⃣  OpenAI API Key (optional, for semantic search)")
        print("   Get your key from: https://platform.openai.com/api-keys")
        current = self.get_openai_api_key()
        if current:
            print(f"   Current: {self.mask_key(current)}")

        new_key = input("   Enter new key (or press Enter to keep current): ").strip()
        if new_key:
            print("   Testing key...")
            if self.validate_openai_key(new_key):
                self.set_openai_api_key(new_key)
                print("   ✅ Key validated and saved!")
            else:
                print("   ❌ Key validation failed. Not saved.")

        # Model Selection
        print("\n3️⃣  Model Selection for Agents")

        available_models = CostCalculator.get_available_models()

        print("\nAvailable models:")
        for idx, model in enumerate(available_models, 1):
            print(f"  {idx}. {model['display_name']}")
            print(f"     ${model['input_price']:.2f}/${model['output_price']:.2f} per MTok")

        # Agent A
        print(f"\n  Agent A (Nova):")
        current_model = self.get_agent_model('agent_a')
        print(f"  Current: {CostCalculator._get_display_name(current_model)}")

        choice = input("  Select model (1-{}), or Enter to keep current: ".format(len(available_models))).strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                self.set_agent_model('agent_a', available_models[idx]['name'])
                print(f"  ✅ Agent A model set to {available_models[idx]['display_name']}")

        # Agent B
        print(f"\n  Agent B (Atlas):")
        current_model = self.get_agent_model('agent_b')
        print(f"  Current: {CostCalculator._get_display_name(current_model)}")

        choice = input("  Select model (1-{}), or Enter to keep current: ".format(len(available_models))).strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_models):
                self.set_agent_model('agent_b', available_models[idx]['name'])
                print(f"  ✅ Agent B model set to {available_models[idx]['display_name']}")

        print("\n" + "="*60)
        print("✅ Configuration complete!")
        print("="*60)


# Singleton instance
_settings_instance: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance


def reset_settings():
    """Reset the global settings instance (useful for testing)."""
    global _settings_instance
    _settings_instance = None
