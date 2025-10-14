"""
Marathon Training App - Strava API Integration
This module handles authentication and data retrieval from Strava API
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StravaAPI:
    """Handles Strava API connections and data retrieval"""
    
    def __init__(self):
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.access_token = os.getenv('STRAVA_ACCESS_TOKEN')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        self.base_url = 'https://www.strava.com/api/v3'
        
    def get_headers(self):
        """Get headers for authenticated requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            print("No refresh token available")
            return False
            
        url = 'https://www.strava.com/oauth/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            
            print("Access token refreshed successfully!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def get_athlete_info(self):
        """Get authenticated athlete information"""
        url = f'{self.base_url}/athlete'
        
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching athlete info: {e}")
            if response.status_code == 401:
                print("Unauthorized - trying to refresh token...")
                if self.refresh_access_token():
                    return self.get_athlete_info()
            return None
    
    def get_activities(self, per_page=30, page=1):
        """Get athlete's activities"""
        url = f'{self.base_url}/athlete/activities'
        params = {
            'per_page': per_page,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching activities: {e}")
            if response.status_code == 401:
                print("Unauthorized - trying to refresh token...")
                if self.refresh_access_token():
                    return self.get_activities(per_page, page)
            return None
    
    def get_running_activities(self, per_page=30):
        """Get only running activities"""
        activities = self.get_activities(per_page)
        if not activities:
            return None
            
        running_activities = [
            activity for activity in activities 
            if activity.get('type') == 'Run'
        ]
        
        return running_activities
    
    def print_athlete_summary(self):
        """Print a summary of athlete information"""
        athlete = self.get_athlete_info()
        if not athlete:
            print("❌ Failed to fetch athlete information")
            return
            
        print("🏃‍♂️ STRAVA ATHLETE INFORMATION")
        print("=" * 40)
        print(f"Name: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        print(f"Username: {athlete.get('username', 'N/A')}")
        print(f"City: {athlete.get('city', 'N/A')}, {athlete.get('state', 'N/A')}")
        print(f"Country: {athlete.get('country', 'N/A')}")
        print(f"Total Followers: {athlete.get('follower_count', 0)}")
        print(f"Total Following: {athlete.get('friend_count', 0)}")
        print(f"Member Since: {athlete.get('created_at', 'N/A')}")
        print()
        
        return athlete
    
    def print_recent_activities(self, limit=10):
        """Print recent activities summary"""
        activities = self.get_activities(per_page=limit)
        if not activities:
            print("❌ Failed to fetch activities")
            return
            
        print(f"📊 RECENT ACTIVITIES (Last {len(activities)})")
        print("=" * 60)
        
        for i, activity in enumerate(activities, 1):
            activity_date = datetime.fromisoformat(
                activity['start_date_local'].replace('Z', '+00:00')
            ).strftime('%Y-%m-%d %H:%M')
            
            distance_km = activity.get('distance', 0) / 1000  # Convert to km
            duration_min = activity.get('moving_time', 0) / 60  # Convert to minutes
            
            print(f"{i:2}. {activity['name']}")
            print(f"    Type: {activity['type']} | Date: {activity_date}")
            print(f"    Distance: {distance_km:.2f} km | Duration: {duration_min:.1f} min")
            
            if activity['type'] == 'Run' and distance_km > 0:
                pace_min_per_km = duration_min / distance_km
                pace_minutes = int(pace_min_per_km)
                pace_seconds = int((pace_min_per_km - pace_minutes) * 60)
                print(f"    Pace: {pace_minutes}:{pace_seconds:02d} min/km")
            
            print()
        
        return activities
    
    def print_running_stats(self):
        """Print running-specific statistics"""
        running_activities = self.get_running_activities(per_page=50)
        if not running_activities:
            print("❌ No running activities found")
            return
            
        print("🏃‍♂️ RUNNING STATISTICS")
        print("=" * 40)
        
        total_distance = sum(activity.get('distance', 0) for activity in running_activities) / 1000
        total_time = sum(activity.get('moving_time', 0) for activity in running_activities) / 3600
        avg_distance = total_distance / len(running_activities) if running_activities else 0
        
        print(f"Total Runs: {len(running_activities)}")
        print(f"Total Distance: {total_distance:.2f} km")
        print(f"Total Time: {total_time:.1f} hours")
        print(f"Average Distance: {avg_distance:.2f} km per run")
        
        if total_distance > 0:
            avg_pace = (total_time * 60) / total_distance  # min/km
            pace_minutes = int(avg_pace)
            pace_seconds = int((avg_pace - pace_minutes) * 60)
            print(f"Average Pace: {pace_minutes}:{pace_seconds:02d} min/km")
        
        print()
        return running_activities


def main():
    """Main function to test Strava API connection"""
    print("🏃‍♂️ Marathon Training App - Strava API Test")
    print("=" * 50)
    
    # Check if environment variables are set
    required_vars = ['STRAVA_CLIENT_ID', 'STRAVA_CLIENT_SECRET', 'STRAVA_ACCESS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with your Strava API credentials.")
        print("Refer to env_example.txt for the required format.")
        return
    
    # Initialize Strava API
    strava = StravaAPI()
    
    # Test API connection and print results
    print("🔗 Testing Strava API connection...\n")
    
    # Get and print athlete information
    athlete = strava.print_athlete_summary()
    
    if athlete:
        # Get and print recent activities
        strava.print_recent_activities(limit=10)
        
        # Get and print running statistics
        strava.print_running_stats()
        
        print("✅ Strava API connection successful!")
    else:
        print("❌ Failed to connect to Strava API")
        print("\nTroubleshooting steps:")
        print("1. Check your API credentials in the .env file")
        print("2. Ensure your access token is valid")
        print("3. Try refreshing your access token")


if __name__ == "__main__":
    main()