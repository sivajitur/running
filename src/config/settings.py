"""
Configuration settings for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (local development only)
load_dotenv()


def _get_secret(key: str, default: str = None) -> str:
    """
    Get a secret from multiple sources in priority order:
    1. Streamlit secrets (deployment platforms, .streamlit/secrets.toml)
    2. Environment variables
    3. Default value
    """
    # Only attempt Streamlit secrets when Streamlit is actually running
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return os.getenv(key, default)


class Settings:
    """Application settings with deployment-friendly configuration."""

    # Strava App Credentials (set by the app owner, not users)
    STRAVA_CLIENT_ID = _get_secret("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = _get_secret("STRAVA_CLIENT_SECRET")
    STRAVA_REFRESH_TOKEN = _get_secret("STRAVA_REFRESH_TOKEN")
    STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
    STRAVA_API_URL = "https://www.strava.com/api/v3"

    # OAuth redirect URI — set to your deployed app URL in production
    # e.g. https://yourapp.streamlit.app for Streamlit Cloud
    REDIRECT_URI = _get_secret("REDIRECT_URI") or "http://localhost:8501"

    # Perplexity API Configuration
    PERPLEXITY_API_KEY = _get_secret("PERPLEXITY_API_KEY")

    # Data Files
    DB_FILE = "running.db"
    CSV_FILE = "strava_activities.csv"
    JSON_FILE = "strava_activities.json"

    @classmethod
    def has_credentials(cls) -> bool:
        """Check if Strava app credentials are configured."""
        return bool(cls.STRAVA_CLIENT_ID and cls.STRAVA_CLIENT_SECRET)
