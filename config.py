import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    # Gemini API Key (check .env first, then shell environment)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Target location for X trends.
    # E.g. 'global' or 'united-states', 'india', 'united-kingdom', etc.
    TRENDS_LOCATION = os.getenv("TRENDS_LOCATION", "global").lower().strip()
    
    # How often the agent runs in background mode (in hours)
    CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", 2))
    
    # Target search query settings
    MAX_SOURCES = int(os.getenv("MAX_SOURCES", 25))
    
    # Model Fallback Chain
    # Read as comma-separated string, default to generic flash model if not provided
    _models_env = os.getenv("GEMINI_MODEL_CHAIN", "gemini-1.5-flash")
    GEMINI_MODEL_CHAIN = [m.strip() for m in _models_env.split(",") if m.strip()]
    
    @classmethod
    def validate(cls):
        """Validate that critical config options are present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing! "
                "Please set it in your .env file or system environment variables."
            )
        return True
