import streamlit as st
import os
from datetime import datetime
import ollama
from analyze_runs import RunAnalyzer
from fetch_strava import StravaAPI

def initialize_session_state():
    if 'strava' not in st.session_state:
        st.session_state.strava = StravaAPI()
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = RunAnalyzer()
    if 'activities' not in st.session_state:
        st.session_state.activities = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def main():
    st.title("🏃‍♂️ Running Coach AI")
    st.write("Your personal AI running coach powered by Strava data")

    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.header("Options")
        days = st.slider("Days of history", 1, 30, 7)
        if st.button("🔄 Refresh Strava Data"):
            with st.spinner("Fetching fresh data from Strava..."):
                try:
                    st.session_state.activities = st.session_state.strava.get_recent_activities(days=days, force_refresh=True)
                    st.success("Data refreshed successfully!")
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")

        st.markdown("---")
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
                st.session_state.activities = st.session_state.strava.get_recent_activities(days=days)
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return

    # Display recent runs
    runs = [a for a in st.session_state.activities if a['type'] == 'Run']
    if runs:
        st.subheader("📊 Your Recent Runs")
        #st.markdown(st.session_state.analyzer.format_runs_for_display(runs))
    else:
        st.info("No running activities found in the selected time period.")

    # Chat interface
    st.markdown("---")
    st.subheader("💬 Chat with your AI Running Coach")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"🤔 **You:** {message['content']}")
        else:
            st.markdown(f"🤖 **Coach:** {message['content']}")
    
    # User input
    user_input = st.text_input(
        "Ask about your running or get recommendations",
        placeholder="e.g., 'What should my next run be?' or 'How am I progressing?'"
    )

    if st.button("Send") and user_input:
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

if __name__ == "__main__":
    main()