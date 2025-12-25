import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys


from utils.parse_json import load_activities_data, get_distance_over_time, get_heart_rate_data, get_elevation_data

def show_page():
    st.title("🏃‍♂️ Run Analysis Dashboard")
    
    # Check if data is available
    if st.session_state.activities is None or len(st.session_state.activities) == 0:
        st.error("No data available. Please refresh Strava data from the Home page.")
        return
    
    # Load data
    df = load_activities_data(st.session_state.activities)
    st.dataframe(df)
    if df.empty:
        st.error("No activities data to analyze")
        return
    
    # Filter by weekday
    st.sidebar.header("Filters")
    weekdays = ["All", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_map = {name: i for i, name in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])}
    selected_weekday = st.sidebar.selectbox("Filter by weekday", weekdays)
    
    weekday_filter = weekday_map.get(selected_weekday) if selected_weekday != "All" else None
    
    # Distance over time
    st.header("Distance Over Time")
    distance_df = get_distance_over_time(df, weekday_filter)
    if not distance_df.empty:
        st.line_chart(distance_df.set_index('date')['Distance (mi)'])
    else:
        st.info("No data for selected filter")
    
    # Heart rate box plot
    st.header("Heart Rate Distribution")
    hr_data = get_heart_rate_data(df)
    if not hr_data.empty:
        fig, ax = plt.subplots()
        ax.boxplot(hr_data)
        ax.set_ylabel("Heart Rate (bpm)")
        ax.set_title("Heart Rate Box Plot")
        st.pyplot(fig)
    else:
        st.info("No heart rate data available")
    
    # Elevation box plot
    st.header("Elevation Gain Distribution")
    elev_data = get_elevation_data(df)
    if elev_data is not None and not elev_data.empty:
        fig, ax = plt.subplots()
        ax.boxplot(elev_data)
        ax.set_ylabel("Elevation Gain (meters)")
        ax.set_title("Elevation Gain Box Plot")
        st.pyplot(fig)
    else:
        st.info("No elevation data available")
    
    # Additional charts
    st.header("Additional Insights")
    
    # Average speed over time
    st.subheader("Average Speed Over Time")
    speed_df = df[['date', 'Average Speed (mph)']].dropna()
    if not speed_df.empty:
        st.line_chart(speed_df.set_index('date')['Average Speed (mph)'])
    
    # Moving time vs Distance
    st.subheader("Moving Time vs Distance")
    time_dist_df = df[['Distance (mi)', 'Moving Time (sec)']].dropna()
    if not time_dist_df.empty:
        st.scatter_chart(time_dist_df.set_index('Distance (mi)')['Moving Time (sec)'])