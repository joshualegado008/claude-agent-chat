"""
Bridge Module - Connects FastAPI to existing Python backend
This module imports and wraps existing functionality without modification
"""

import sys
from pathlib import Path

# Add parent directory to Python path to import existing modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import existing modules (unchanged)
from db_manager import DatabaseManager
from conversation_manager_persistent import PersistentConversationManager, ConversationBrowser
from agent_runner import AgentPool, Agent
from cost_calculator import CostCalculator
from settings_manager import SettingsManager, get_settings
from display_formatter import DisplayFormatter

# Initialize settings with correct path to root settings.json
# This must happen before DatabaseManager initialization
_root_settings_path = parent_dir / 'settings.json'
import settings_manager
if settings_manager._settings_instance is None:
    settings_manager._settings_instance = SettingsManager(str(_root_settings_path))

# Optional imports for rich features
try:
    from metadata_extractor import MetadataExtractor
    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False


class BackendBridge:
    """
    Bridge class that provides a clean interface for the web API
    to interact with existing Python backend code.
    """

    def __init__(self):
        """Initialize database and settings."""
        self.db = DatabaseManager()
        self.settings = get_settings()

        # Initialize metadata extractor if OpenAI key available
        self.metadata_extractor = None
        print(f"🔍 DEBUG: Initializing BackendBridge")
        print(f"   METADATA_AVAILABLE: {METADATA_AVAILABLE}")

        if METADATA_AVAILABLE:
            try:
                openai_key = self.settings.get_openai_api_key()
                print(f"   OpenAI key from settings: {'***' + openai_key[-4:] if openai_key else 'None'}")
                if openai_key:
                    self.metadata_extractor = MetadataExtractor(api_key=openai_key)
                    print(f"   ✅ MetadataExtractor initialized successfully")
                else:
                    print(f"   ⚠️  OpenAI key not found in settings")
            except Exception as e:
                print(f"   ❌ Warning: Metadata extractor not available: {e}")

    def get_database_manager(self) -> DatabaseManager:
        """Get the database manager instance."""
        return self.db

    def get_conversation_browser(self) -> ConversationBrowser:
        """Get a conversation browser instance."""
        return ConversationBrowser(self.db)

    def create_conversation_manager(self) -> PersistentConversationManager:
        """Create a new conversation manager instance."""
        return PersistentConversationManager(self.db)

    def create_agent_pool(self) -> AgentPool:
        """Create a new agent pool."""
        return AgentPool()

    def get_settings(self):
        """Get settings manager."""
        return self.settings

    def get_metadata_extractor(self):
        """Get metadata extractor if available."""
        return self.metadata_extractor

    def close(self):
        """Close database connections."""
        if self.db:
            self.db.close()


# Global bridge instance (singleton pattern)
_bridge = None

def get_bridge() -> BackendBridge:
    """Get or create the global bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = BackendBridge()
    return _bridge
