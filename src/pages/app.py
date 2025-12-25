import streamlit as st
import os
import sys
from datetime import datetime

from pages.analyze_run_ui import show_page as show_analysis_page
from pages.llm_analysis_ui import show_page as show_llm_page
from pages.home_ui import show_page as show_home_page

from utils.analyze_run import RunAnalyzer
from utils.fetch_strava import StravaAPI

def initialize_session_state():
    if 'strava' not in st.session_state:
        st.session_state.strava = StravaAPI()
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = RunAnalyzer()
    if 'activities' not in st.session_state:
        st.session_state.activities = None
        # Try to load from cache on startup
        st.session_state.activities = st.session_state.strava.get_recent_activities(days=30, force_refresh=False)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def main():
    initialize_session_state()
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Run Analysis", "AI Coach"])
    
    # Common sidebar elements
    st.sidebar.header("Data Options")
    days = st.sidebar.slider("Days of history", 1, 365, 30)  # Increased max to 365
    if st.sidebar.button("🔄 Refresh Strava Data"):
        with st.spinner("Fetching fresh data from Strava..."):
            try:
                st.session_state.activities = st.session_state.strava.get_recent_activities(days=days, force_refresh=True)
                st.success("Data refreshed successfully!")
            except Exception as e:
                st.sidebar.error(f"Error fetching data: {str(e)}")
    
    if page == "Home":
        show_home_page()
    elif page == "Run Analysis":
        show_analysis_page()
    elif page == "AI Coach":
        show_llm_page()

if __name__ == "__main__":
    main()