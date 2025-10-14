"""
Helper script to get Strava API access token
This script helps you obtain the initial access token for Strava API
"""

import os
import requests
from dotenv import load_dotenv

def get_authorization_url():
    """Generate the authorization URL for Strava OAuth"""
    load_dotenv()
    client_id = os.getenv('STRAVA_CLIENT_ID')
    
    if not client_id:
        print("❌ STRAVA_CLIENT_ID not found in .env file")
        return None
    
    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri=http://localhost&"
        f"approval_prompt=force&"
        f"scope=read,activity:read_all"
    )
    
    return auth_url

def exchange_code_for_token(authorization_code):
    """Exchange authorization code for access token"""
    load_dotenv()
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET not found in .env file")
        return None
    
    url = 'https://www.strava.com/oauth/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error exchanging code for token: {e}")
        return None

def main():
    """Main function to guide user through OAuth process"""
    print("🏃‍♂️ Strava API Access Token Setup")
    print("=" * 40)
    
    # Check if client credentials are set
    load_dotenv()
    if not os.getenv('STRAVA_CLIENT_ID') or not os.getenv('STRAVA_CLIENT_SECRET'):
        print("❌ Please set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in your .env file first")
        print("You can get these from https://developers.strava.com/")
        return
    
    print("Step 1: Get authorization URL")
    auth_url = get_authorization_url()
    if not auth_url:
        return
    
    print(f"\n📋 Copy this URL and open it in your browser:")
    print(f"{auth_url}")
    print(f"\n📝 After authorizing, you'll be redirected to a URL like:")
    print(f"http://localhost/?state=&code=AUTHORIZATION_CODE&scope=read,activity:read_all")
    
    # Get authorization code from user
    print(f"\nStep 2: Copy the authorization code from the redirect URL")
    auth_code = input("Enter the authorization code: ").strip()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return
    
    print(f"\nStep 3: Exchange code for access token...")
    token_data = exchange_code_for_token(auth_code)
    
    if not token_data:
        return
    
    print(f"\n✅ Success! Here are your tokens:")
    print(f"Access Token: {token_data['access_token']}")
    print(f"Refresh Token: {token_data['refresh_token']}")
    print(f"Expires At: {token_data['expires_at']}")
    
    print(f"\n📝 Add these to your .env file:")
    print(f"STRAVA_ACCESS_TOKEN={token_data['access_token']}")
    print(f"STRAVA_REFRESH_TOKEN={token_data['refresh_token']}")

if __name__ == "__main__":
    main()