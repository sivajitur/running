import streamlit as st
import os
import sys
import json



from utils.analyze_run import RunAnalyzer
from utils.fetch_strava import StravaAPI

def initialize_session_state():
    if 'strava' not in st.session_state:
        try:
            st.session_state.strava = StravaAPI()
        except ValueError as e:
            st.session_state.strava = None
            st.session_state.auth_error = str(e)
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = RunAnalyzer()
    if 'activities' not in st.session_state:
        st.session_state.activities = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def show_page():
    st.title("🏃‍♂️ Welcome to Running Coach AI")
    
    st.markdown("""
    # Your Personal AI Running Coach
    
    Transform your running data into actionable insights with our AI-powered analysis platform.
    
    ## Features:
    - 📊 **Run Analysis**: Visualize your running patterns with interactive charts
    - 🤖 **AI Coach**: Get personalized training advice and recommendations
    - 📈 **Performance Tracking**: Monitor your progress over time
    - 💬 **Chat Interface**: Ask questions about your running in natural language
    
    ## Get Started:
    Connect your Strava account to access your running data and unlock all features.
    """)
    
    initialize_session_state()
    
    # Check for OAuth callback
    query_params = st.query_params
    if 'code' in query_params:
        code = query_params['code']
        try:
            with st.spinner("Connecting to Strava..."):
                if st.session_state.strava:
                    st.session_state.strava.exchange_code_for_tokens(code)
                    st.success("✅ Successfully connected to Strava!")
                    st.query_params.clear()  # Clear the code from URL
                    st.rerun()
                else:
                    st.error("Strava API not configured properly")
        except Exception as e:
            st.error(f"Failed to connect: {str(e)}")
    
    # Check authentication status
    if st.session_state.strava and st.session_state.strava.is_authenticated():
        mode_text = " (Offline Mode)" if getattr(st.session_state.strava, 'offline_mode', False) else ""
        st.success(f"✅ Connected to Strava{mode_text}! Your data is ready.")
        
        st.markdown("Use the navigation sidebar to explore your data and chat with the AI coach.")
        
        # Option to fetch more data
        if not getattr(st.session_state.strava, 'offline_mode', False):
            st.markdown("---")
            st.subheader("Data Management")
            if st.button("🔄 Fetch All Available Runs"):
                with st.spinner("Fetching all your running data..."):
                    try:
                        st.session_state.activities = st.session_state.strava.get_recent_activities(days=365, force_refresh=True)
                        st.success("All available runs fetched successfully!")
                    except Exception as e:
                        st.error(f"Error fetching data: {str(e)}")
        else:
            st.info("📁 Working with cached data. To fetch new data, configure Strava API credentials.")
    else:
        # Check if we have cached data to work with
        if os.path.exists('strava_activities_raw.json'):
            st.info("📁 Found cached data! Working in offline mode.")
            st.markdown("You can explore your previously loaded running data using the navigation.")
            
            # Load cached data
            if st.session_state.activities is None:
                try:
                    with open('strava_activities_raw.json', 'r') as f:
                        cached_data = json.load(f)
                        st.session_state.activities = cached_data['activities']
                    st.success("Cached data loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading cached data: {str(e)}")
        else:
            st.warning("⚠️ No Strava connection or cached data found.")
            
            if st.session_state.strava is None:
                if 'auth_error' in st.session_state:
                    st.error(f"Configuration Error: {st.session_state.auth_error}")
                st.markdown(f"""
                **Setup Required**: Please ensure your Strava app credentials are configured:
                
                - Create a Strava app at https://www.strava.com/settings/api
                - Set `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` in your environment
                - **Important**: Set the redirect URI in your Strava app to exactly: `{st.session_state.strava.redirect_uri if st.session_state.strava else 'http://localhost:8505'}`
                
                The redirect URI must exactly match what's configured in your Strava app settings.
                """)
            else:
                auth_url = st.session_state.strava.get_authorization_url()
                if auth_url:
                    st.markdown(f"[🔗 Connect to Strava]({auth_url})")
                    st.markdown("""
                    **Click the link above to authorize the app with your Strava account.**
                    
                    After authorization, you'll be redirected back here automatically.
                    """)
                else:
                    st.info("Offline mode active - no authorization needed.")
                    
        if st.button("🔄 Check Connection"):
            st.rerun()