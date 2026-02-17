"""
Strava Authentication Page
"""

import streamlit as st
import os
from urllib.parse import urlparse, parse_qs
from src.auth import StravaOAuthHandler
from src.config import Settings


def get_auth_handler() -> StravaOAuthHandler:
    """Get OAuth handler with app credentials."""
    settings = Settings()
    return StravaOAuthHandler(
        client_id=settings.STRAVA_CLIENT_ID,
        client_secret=settings.STRAVA_CLIENT_SECRET,
        redirect_uri="http://localhost:8501",
    )


def show_auth_page():
    """Display authentication page for users to log in with Strava."""
    
    st.set_page_config(
        page_title="Strava Running Analytics - Sign In",
        page_icon="🏃",
        layout="centered"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("https://cdn2.strava.com/logo_files/strava_logo-1e6ce0ed2f3cc1f4eee8c8be12d7e2ba.svg", width=200)
        st.title("Running Analytics")
        st.markdown("---")
        
        st.markdown("""
        ## Welcome! 🏃‍♂️
        
        This dashboard analyzes your **Strava running data** and provides:
        
        - 📊 **Activity Tracking** - View all your runs over time
        - 📈 **Performance Metrics** - Distance, pace, heart rate analytics
        - 🗓️ **Weekly Insights** - Trends by day of week
        - 💬 **AI Coach** - Get personalized advice from Perplexity
        - 🔐 **Your Data** - All stored locally, never shared
        
        ### Getting Started
        """)
        
        auth_handler = get_auth_handler()
        auth_url = auth_handler.get_authorization_url()
        
        st.markdown(f"""
        **Step 1:** Click the button below to authorize with Strava
        
        **Step 2:** You'll be redirected back with an authorization code
        
        **Step 3:** Paste the code below to complete sign-in
        """)
        
        # Authorization button
        st.link_button(
            "🔗 Authorize with Strava",
            url=auth_url,
            use_container_width=True,
            type="primary"
        )
        
        st.markdown("---")
        
        # Check for authorization code in query params
        query_params = st.query_params
        
        if "code" in query_params:
            auth_code = query_params["code"]
            
            st.success("✅ Authorization code received!")
            
            st.info(f"**Your Authorization Code:**\n```\n{auth_code}\n```")
            
            st.markdown("Paste this code below to complete authentication:")
        
        # Manual code entry
        st.markdown("### Or Paste Your Authorization Code")
        
        auth_code = st.text_input(
            "Authorization Code:",
            placeholder="e.g., abc123xyz...",
            type="password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Authenticate", use_container_width=True, type="primary"):
                if not auth_code:
                    st.error("Please enter an authorization code")
                else:
                    with st.spinner("Authenticating with Strava..."):
                        try:
                            token = auth_handler.exchange_code_for_token(auth_code)
                            
                            # Store token in session
                            st.session_state.strava_token = token.to_dict()
                            st.session_state.authenticated = True
                            
                            st.success(f"✅ Welcome, {token.athlete_name}!")
                            st.info("Redirecting to dashboard...")
                            
                            # Redirect to main app
                            st.switch_page("pages/dashboard.py")
                        
                        except Exception as e:
                            st.error(f"❌ Authentication failed: {str(e)}")
        
        with col2:
            if st.button("🔄 Try Again", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        ### Privacy & Security
        
        - 🔐 Your tokens are stored only in your browser session
        - 📱 No data is stored on our servers
        - 🚫 We only request permission to read your activity data
        - 🗑️ Refresh to clear your data
        """)


if __name__ == "__main__":
    show_auth_page()
