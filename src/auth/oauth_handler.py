"""
Strava OAuth 2.0 Handler for user authentication.
"""

import requests
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class StravaToken:
    """Container for Strava OAuth tokens."""
    access_token: str
    refresh_token: str
    expires_at: int
    athlete_id: int
    athlete_name: str
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now().timestamp() > self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at,
            'athlete_id': self.athlete_id,
            'athlete_name': self.athlete_name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StravaToken':
        """Create from dictionary."""
        return cls(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            expires_at=data['expires_at'],
            athlete_id=data['athlete_id'],
            athlete_name=data['athlete_name'],
        )


class StravaOAuthHandler:
    """Handles Strava OAuth 2.0 authentication flow."""
    
    STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
    STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8501"):
        """
        Initialize OAuth handler.
        
        Args:
            client_id: Strava app client ID
            client_secret: Strava app client secret
            redirect_uri: OAuth callback URL (default Streamlit local)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_authorization_url(self, scope: str = "read,activity:read") -> str:
        """
        Generate Strava OAuth authorization URL.
        
        Args:
            scope: OAuth scopes to request
            
        Returns:
            Authorization URL for user to visit
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope,
            "approval_prompt": "force",
        }
        
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.STRAVA_AUTH_URL}?{param_string}"
    
    def exchange_code_for_token(self, code: str) -> StravaToken:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            StravaToken object with tokens and athlete info
            
        Raises:
            ValueError: If token exchange fails
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        
        try:
            response = requests.post(self.STRAVA_TOKEN_URL, data=payload)
            response.raise_for_status()
            
            data = response.json()
            
            athlete = data.get('athlete', {})
            
            token = StravaToken(
                access_token=data['access_token'],
                refresh_token=data['refresh_token'],
                expires_at=data['expires_at'],
                athlete_id=athlete.get('id', 0),
                athlete_name=athlete.get('firstname', 'Athlete'),
            )
            
            return token
        
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"Failed to exchange code for token: {e.response.text}")
    
    def refresh_access_token(self, refresh_token: str) -> StravaToken:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: User's refresh token
            
        Returns:
            New StravaToken with updated tokens
            
        Raises:
            ValueError: If token refresh fails
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        try:
            response = requests.post(self.STRAVA_TOKEN_URL, data=payload)
            response.raise_for_status()
            
            data = response.json()
            
            token = StravaToken(
                access_token=data['access_token'],
                refresh_token=data['refresh_token'],
                expires_at=data['expires_at'],
                athlete_id=data.get('athlete', {}).get('id', 0),
                athlete_name=data.get('athlete', {}).get('firstname', 'Athlete'),
            )
            
            return token
        
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"Failed to refresh token: {e.response.text}")
