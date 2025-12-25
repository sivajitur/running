import streamlit as st
import os
import sys
from datetime import datetime


from utils.analyze_run import RunAnalyzer
from utils.fetch_strava import StravaAPI
from utils.parse_json import load_activities_data

def initialize_session_state():
    if 'strava' not in st.session_state:
        st.session_state.strava = StravaAPI()
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = RunAnalyzer()
    if 'activities' not in st.session_state:
        st.session_state.activities = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def show_page():
    st.title("🏃‍♂️ Running Coach AI")
    st.write("Your personal AI running coach powered by Strava data")

    initialize_session_state()

    # Sidebar for coach page specific options
    with st.sidebar:
        st.markdown("""
        ### How to use
        1. Refresh your Strava data using the button above
        2. View your recent runs in the main panel
        3. Ask questions about your running or get recommendations
        4. The AI coach will analyze your data and provide personalized advice
        """)

    # Main content
    if st.session_state.activities is None:
        try:
            with st.spinner("Loading your running data..."):
                st.session_state.activities = st.session_state.strava.get_recent_activities(days=7)  # Default to 7 days
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return

    # Display recent runs
    runs = [a for a in st.session_state.activities if a['type'] == 'Run']
    if runs:
        st.subheader("📊 Your Recent Runs")
        df = load_activities_data(runs)
        st.dataframe(df.head(len(df) - 1))
    else:
        st.info("No running activities found in the selected time period.")

    # Chat interface
    st.markdown("---")
    st.subheader("💬 Chat with your AI Running Coach")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message['content'])
    
    # User input
    if user_input := st.chat_input("Ask about your running or get recommendations"):
        with st.spinner("Analyzing your running data..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Get AI response
            response = st.session_state.analyzer.analyze_runs(
                activities = st.session_state.activities,
                user_question=user_input
            )
            
            # Add AI response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # Rerun to update the display
            st.rerun()
