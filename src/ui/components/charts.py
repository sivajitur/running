"""
Chart and visualization components.
"""

import streamlit as st
import plotly.express as px
import pandas as pd


class ChartsComponent:
    """Create interactive charts."""
    
    @staticmethod
    def distance_over_time(filtered_runs: pd.DataFrame, grouping: str) -> None:
        """
        Display distance over time chart.
        
        Args:
            filtered_runs: Filtered runs DataFrame
            grouping: Grouping period ('Day', 'Week', or 'Month')
        """
        if grouping == "Day":
            daily_distance = filtered_runs.groupby('date').agg({
                'distance_miles': 'sum',
                'type': 'count'
            }).reset_index()
            daily_distance.columns = ['Date', 'Distance', 'Runs']
            
            fig = px.bar(
                daily_distance,
                x='Date',
                y='Distance',
                title="Daily Distance",
                labels={'Distance': 'Distance (miles)', 'Date': 'Date'},
                color='Distance',
                color_continuous_scale='Blues'
            )
        
        elif grouping == "Week":
            weekly_distance = filtered_runs.groupby('week_start').agg({
                'distance_miles': 'sum',
                'type': 'count'
            }).reset_index()
            weekly_distance.columns = ['Week Start', 'Distance', 'Runs']
            
            fig = px.bar(
                weekly_distance,
                x='Week Start',
                y='Distance',
                title="Weekly Distance",
                labels={'Distance': 'Distance (miles)', 'Week Start': 'Week Starting'},
                color='Distance',
                color_continuous_scale='Greens'
            )
        
        else:  # Month
            monthly_distance = filtered_runs.groupby('year_month').agg({
                'distance_miles': 'sum',
                'type': 'count'
            }).reset_index()
            monthly_distance.columns = ['Month', 'Distance', 'Runs']
            
            fig = px.bar(
                monthly_distance,
                x='Month',
                y='Distance',
                title="Monthly Distance",
                labels={'Distance': 'Distance (miles)', 'Month': 'Month'},
                color='Distance',
                color_continuous_scale='Purples'
            )
        
        fig.update_layout(height=500, hovermode='x unified')
        st.plotly_chart(fig, width='stretch')
    
    @staticmethod
    def runs_by_day(day_stats: pd.DataFrame) -> None:
        """
        Display runs and distance by day of week.
        
        Args:
            day_stats: Day statistics DataFrame
        """
        col1, col2 = st.columns(2)
        
        with col1:
            fig_runs = px.bar(
                day_stats,
                x='Day',
                y='Runs',
                title="Number of Runs by Day",
                labels={'Runs': 'Count', 'Day': 'Day of Week'},
                color='Runs',
                color_continuous_scale='Blues'
            )
            fig_runs.update_layout(height=400)
            st.plotly_chart(fig_runs, width='stretch')
        
        with col2:
            fig_distance = px.bar(
                day_stats,
                x='Day',
                y='Total Distance',
                title="Total Distance by Day",
                labels={'Total Distance': 'Miles', 'Day': 'Day of Week'},
                color='Total Distance',
                color_continuous_scale='Greens'
            )
            fig_distance.update_layout(height=400)
            st.plotly_chart(fig_distance, width='stretch')
    
    @staticmethod
    def distance_distribution(filtered_runs: pd.DataFrame) -> None:
        """
        Display distance distribution histogram.
        
        Args:
            filtered_runs: Filtered runs DataFrame
        """
        fig = px.histogram(
            filtered_runs,
            x='distance_miles',
            nbins=20,
            title="Distribution of Run Distances",
            labels={'distance_miles': 'Distance (miles)', 'count': 'Frequency'},
            color_discrete_sequence=['#636EFA']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')
    
    @staticmethod
    def heart_rate_vs_distance(filtered_runs: pd.DataFrame) -> None:
        """
        Display heart rate vs distance scatter plot.
        
        Args:
            filtered_runs: Filtered runs DataFrame
        """
        fig = px.scatter(
            filtered_runs.dropna(subset=['average_heartrate_bpm']),
            x='distance_miles',
            y='average_heartrate_bpm',
            title="Average Heart Rate vs Distance",
            labels={
                'distance_miles': 'Distance (miles)',
                'average_heartrate_bpm': 'Avg Heart Rate (bpm)'
            },
            color='average_heartrate_bpm',
            color_continuous_scale='Viridis',
            hover_data=['date', 'pace_min_per_mile']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')
