"""
Strava API client for retrieving activity data.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..config import Settings


class StravaClient:
    """Client for interacting with the Strava API."""
    
    def __init__(self, access_token: str = None):
        """
        Initialize the Strava client.
        
        Args:
            access_token: Optional access token. If provided, use it directly.
                         If not provided, will use refresh token from Settings.
        """
        self.client_id = Settings.STRAVA_CLIENT_ID
        self.client_secret = Settings.STRAVA_CLIENT_SECRET
        self.refresh_token = Settings.STRAVA_REFRESH_TOKEN
        self.access_token = access_token
        self.token_expires_at = None
        
    def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token for Strava API
        """
        # If we have a directly provided access token, return it
        if self.access_token:
            return self.access_token
        
        # If no refresh token available, raise error
        if not self.refresh_token:
            raise ValueError("No access token or refresh token available")
        
        # Refresh the token
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        
        try:
            response = requests.post(Settings.STRAVA_TOKEN_URL, data=payload)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires_at = data["expires_at"]
            
            return self.access_token
        
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Token refresh failed: {e.response.status_code} - {e.response.text}")
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get headers with authorization for API requests.
        
        Returns:
            Dict: Headers with Bearer token
        """
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def get_activities(self, months_back: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieve activities from the past N months.
        
        Args:
            months_back: Number of months to retrieve activities for (default: 6)
            
        Returns:
            List: Raw activity data from Strava
        """
        # Calculate the date from N months ago
        now = datetime.now()
        past_date = now - timedelta(days=30 * months_back)
        after_timestamp = int(past_date.timestamp())
        
        all_activities = []
        page = 1
        per_page = 200  # Maximum allowed by Strava API
        
        while True:
            url = f"{Settings.STRAVA_API_URL}/athlete/activities"
            params = {
                "after": after_timestamp,
                "page": page,
                "per_page": per_page,
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            activities = response.json()
            
            if not activities:
                break
            
            all_activities.extend(activities)
            page += 1
            
            # If we got fewer items than per_page, we've reached the end
            if len(activities) < per_page:
                break
        
        return all_activities
