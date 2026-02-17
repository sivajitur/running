"""
Configuration settings for the application.
"""

import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file (local development only)
load_dotenv()


class Settings:
    """Application settings with deployment-friendly configuration."""
    
    @classmethod
    def _get_secret(cls, key: str, default: str = None) -> str:
        """
        Get a secret from multiple sources in priority order:
        1. Streamlit secrets (deployment platforms, .streamlit/secrets.toml)
        2. Environment variables (set by deployment platform)
        3. Default value
        
        This allows deployment without modifying source code.
        """
        try:
            return st.secrets.get(key, default)
        except FileNotFoundError:
            return os.getenv(key, default)
    
    # Strava API Configuration
    STRAVA_CLIENT_ID = _get_secret.__func__(None, "STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = _get_secret.__func__(None, "STRAVA_CLIENT_SECRET")
    STRAVA_REFRESH_TOKEN = _get_secret.__func__(None, "STRAVA_REFRESH_TOKEN")
    STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
    STRAVA_API_URL = "https://www.strava.com/api/v3"
    
    # Perplexity API Configuration
    PERPLEXITY_API_KEY = _get_secret.__func__(None, "PERPLEXITY_API_KEY")
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    PERPLEXITY_MODEL = "sonar-small-online"
    
    # Data Files
    CSV_FILE = "strava_activities.csv"
    JSON_FILE = "strava_activities.json"
    
    @classmethod
    def set_credentials(cls, client_id: str, client_secret: str) -> None:
        """Allow setting credentials programmatically (for UI setup)."""
        cls.STRAVA_CLIENT_ID = client_id
        cls.STRAVA_CLIENT_SECRET = client_secret
    
    @classmethod
    def has_credentials(cls) -> bool:
        """Check if Strava credentials are configured."""
        return bool(cls.STRAVA_CLIENT_ID and cls.STRAVA_CLIENT_SECRET)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required settings are configured."""
        required = [
            cls.STRAVA_CLIENT_ID,
            cls.STRAVA_CLIENT_SECRET,
            cls.STRAVA_REFRESH_TOKEN,
        ]
        return all(required)
