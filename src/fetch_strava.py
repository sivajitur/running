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
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://www.strava.com/api/v3"
        self.data_file = 'strava_activities_raw.json'

    def _refresh_access_token(self):
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
        self.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])

    def _ensure_token_valid(self):
        if not self.access_token or not self.token_expires_at or datetime.now() >= self.token_expires_at:
            self._refresh_access_token()

    def get_recent_activities(self, days=30, force_refresh=False):
        """
        Get activities from Strava API or load from cached file if available
        :param days: Number of days to look back
        :param force_refresh: If True, fetch from API regardless of cache
        :return: List of activities
        """
        # Check if we have cached data and it's recent enough
        if not force_refresh and os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                cached_data = json.load(f)
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                # Use cache if it's less than 3 hours old
                if datetime.now() - cache_time < timedelta(hours=3):
                    print("Using cached Strava data...")
                    return cached_data['activities']

        print("Fetching fresh data from Strava...")
        self._ensure_token_valid()
        after_date = int((datetime.now() - timedelta(days=days)).timestamp())
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {
            'after': after_date,
            'per_page': 30
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
            dic = {'date': activity['start_date'], 'distance': activity['distance'], 'moving_time': activity['moving_time'], 'elapsed_time': activity['elapsed_time'], 'average_speed': activity['average_speed'], 'max_speed': activity['max_speed']}
            if activity['has_heartrate']:
                dic['average_heartrate'] = activity['average_heartrate']
                dic['max_heartrate'] = activity['max_heartrate']
            else:
                dic['average_heartrate'] = None
                dic['max_heartrate'] = None
            activities[activity['start_date'][:10]] = dic

        with open('strava_activities.json', 'w') as f:
            json.dump(activities, f, indent=4)

def main():
    try:
        strava = StravaAPI()
        
        # Get activities with optional force refresh
        force_refresh = '--force' in os.sys.argv
        activities = strava.get_recent_activities(force_refresh=False)
        parsed_activities = strava.parse_and_save_activities(data = activities)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()