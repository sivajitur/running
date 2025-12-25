import os
from datetime import datetime, timedelta
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StravaAPI:
    def __init__(self):
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = None
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://www.strava.com/api/v3"
        self.data_file = 'strava_activities_raw.json'
        self.tokens_file = 'strava_tokens.json'
        self.redirect_uri = "http://localhost:8505"  # Must match Strava app settings
        
        # Try to load tokens from file
        self._load_tokens()
        
        # If no client credentials but we have tokens, we can work offline
        if not self.client_id or not self.client_secret:
            if self.refresh_token:
                # We have cached tokens, work in offline mode
                self.offline_mode = True
            else:
                raise ValueError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in environment variables, or valid tokens must exist")
        else:
            self.offline_mode = False

    def _load_tokens(self):
        if os.path.exists(self.tokens_file):
            with open(self.tokens_file, 'r') as f:
                token_data = json.load(f)
                self.refresh_token = token_data.get('refresh_token')
                self.access_token = token_data.get('access_token')
                if token_data.get('expires_at'):
                    self.token_expires_at = datetime.fromtimestamp(token_data['expires_at'])

    def _save_tokens(self):
        token_data = {
            'refresh_token': self.refresh_token,
            'access_token': self.access_token,
            'expires_at': self.token_expires_at.timestamp() if self.token_expires_at else None
        }
        with open(self.tokens_file, 'w') as f:
            json.dump(token_data, f)

    def get_authorization_url(self):
        """Generate Strava authorization URL"""
        if self.offline_mode:
            return None
        auth_url = "https://www.strava.com/oauth/authorize"
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'read,activity:read_all'
        }
        from urllib.parse import urlencode
        return f"{auth_url}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code):
        """Exchange authorization code for access and refresh tokens"""
        if self.offline_mode:
            return False
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(auth_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
        
        self._save_tokens()
        return True

    def _refresh_access_token(self):
        if self.offline_mode or not self.refresh_token:
            # In offline mode, assume tokens are still valid
            return
            
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        response = requests.post(auth_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
        self._save_tokens()

    def _ensure_token_valid(self):
        if self.offline_mode:
            # In offline mode, assume tokens are valid
            return
        if not self.access_token or not self.token_expires_at or datetime.now() >= self.token_expires_at:
            self._refresh_access_token()

    def is_authenticated(self):
        """Check if we have valid tokens"""
        return self.refresh_token is not None

    def get_recent_activities(self, days=30, force_refresh=False):
        """
        Get activities from Strava API or load from cached file if available
        :param days: Number of days to look back
        :param force_refresh: If True, fetch from API regardless of cache
        :return: List of activities
        """
        # Check if we have cached data
        if not force_refresh and os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                cached_data = json.load(f)
                print("Using cached Strava data...")
                return cached_data['activities']

        if self.offline_mode:
            print("Offline mode: no cached data available")
            return []

        if not force_refresh:
            print("No cached data and not refreshing")
            return []

        print("Fetching fresh data from Strava...")
        self._ensure_token_valid()
        after_date = int((datetime.now() - timedelta(days=days)).timestamp())
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {
            'after': after_date,
            'per_page': 200  # Increased from 30 to 200 (Strava's maximum)
        }
        
        response = requests.get(f"{self.base_url}/athlete/activities", headers=headers, params=params)
        response.raise_for_status()
        activities = response.json()

        # Save to file with timestamp
        data_to_save = {
            'timestamp': datetime.now().isoformat(),
            'activities': activities
        }
        with open(self.data_file, 'w') as f:
            json.dump(data_to_save, f, indent=2)

        return activities
    
    def parse_and_save_activities(self, data):
        activities = {}
        for activity in data:
            dic = {'date': activity['start_date'], 'distance': activity['distance'], 'moving_time': activity['moving_time'], 'elapsed_time': activity['elapsed_time'], 'average_speed': activity['average_speed'], 'max_speed': activity['max_speed'], 'total_elevation_gain': activity.get('total_elevation_gain', 0)}
            if activity['has_heartrate']:
                dic['average_heartrate'] = activity['average_heartrate']
                dic['max_heartrate'] = activity['max_heartrate']
            else:
                dic['average_heartrate'] = None
                dic['max_heartrate'] = None
            activities[activity['start_date'][:10]] = dic

        with open('fucku_strava_activities.json', 'w') as f:
            json.dump(activities, f, indent=4)

def main():
    try:
        strava = StravaAPI()
        
        # Get activities with optional force refresh
        force_refresh = '--force' in os.sys.argv
        activities = strava.get_recent_activities(days=120, force_refresh=True)
        parsed_activities = strava.parse_and_save_activities(data=activities)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()