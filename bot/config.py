"""
Configuration loader for the bot.

Loads environment variables from .env.bot.secret file.
"""

import os
from pathlib import Path


def load_config() -> dict:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary with configuration values
    """
    # Try to load from .env.bot.secret file
    env_file = Path(__file__).parent.parent / ".env.bot.secret"
    
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
    
    return {
        "bot_token": os.environ.get("BOT_TOKEN", ""),
        "lms_api_base_url": os.environ.get("LMS_API_BASE_URL", ""),
        "lms_api_key": os.environ.get("LMS_API_KEY", ""),
        "llm_api_key": os.environ.get("LLM_API_KEY", ""),
        "llm_api_base_url": os.environ.get("LLM_API_BASE_URL", ""),
        "llm_api_model": os.environ.get("LLM_API_MODEL", "coder-model"),
    }
