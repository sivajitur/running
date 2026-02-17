"""
Main Streamlit application with Authentication.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time

from ..config import Settings
from ..data import DataProcessor
from ..analysis import RunningAnalyzer, PerplexityClient
from ..auth import StravaOAuthHandler, StravaToken
from .components import MetricsComponent, ChartsComponent, AITabComponent


class StreamlitApp:
    """Main Streamlit application."""
    
    def __init__(self):
        """Initialize the application."""
        self._setup_page()
        self._setup_session_state()
    
    def _setup_session_state(self) -> None:
        """Initialize session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'strava_token' not in st.session_state:
            st.session_state.strava_token = None
    
    def _setup_page(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Strava Running Analytics",
            page_icon="🏃",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.markdown("""
            <style>
            .metric-card {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
            </style>
        """, unsafe_allow_html=True)
    
    @st.cache_data
    def load_data(_self):
        """Load and prepare data."""
        df = DataProcessor.load_csv()
        return df
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated."""
        if not st.session_state.authenticated:
            self._show_auth_page()
            return False
        return True
    
    def _show_auth_page(self) -> None:
        """Display authentication page."""
        st.set_page_config(layout="centered")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.image("https://cdn2.strava.com/logo_files/strava_logo-1e6ce0ed2f3cc1f4eee8c8be12d7e2ba.svg", width=150)
            st.title("Running Analytics")
            st.markdown("---")
            
            st.markdown("""
            ### Welcome! 🏃‍♂️
            
            Analyze your Strava running data with:
            - 📊 Activity tracking
            - 📈 Performance metrics
            - 🗓️ Weekly insights
            - 💬 AI coaching
            """)
            
            settings = Settings()
            auth_handler = StravaOAuthHandler(
                client_id=settings.STRAVA_CLIENT_ID,
                client_secret=settings.STRAVA_CLIENT_SECRET,
                redirect_uri="http://localhost:8501",
            )
            
            auth_url = auth_handler.get_authorization_url()
            st.link_button(
                "🔗 Authorize with Strava",
                url=auth_url,
                use_container_width=True,
                type="primary"
            )
            
            st.markdown("---")
            
            # Check for auth code
            if "code" in st.query_params:
                auth_code = st.query_params["code"]
                
                with st.spinner("Authenticating..."):
                    try:
                        token = auth_handler.exchange_code_for_token(auth_code)
                        st.session_state.strava_token = token.to_dict()
                        st.session_state.authenticated = True
                        st.success(f"✅ Welcome, {token.athlete_name}!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Authentication failed: {str(e)}")
            
            # Manual code entry
            auth_code = st.text_input(
                "Or paste your authorization code:",
                placeholder="abc123xyz...",
                type="password"
            )
            
            if st.button("✅ Authenticate", use_container_width=True, type="primary"):
                if not auth_code:
                    st.error("Please enter an authorization code")
                else:
                    with st.spinner("Authenticating..."):
                        try:
                            token = auth_handler.exchange_code_for_token(auth_code)
                            st.session_state.strava_token = token.to_dict()
                            st.session_state.authenticated = True
                            st.success(f"✅ Welcome, {token.athlete_name}!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Authentication failed: {str(e)}")
        
        st.stop()
    
    def _show_logout_button(self) -> None:
        """Show logout button in sidebar."""
        with st.sidebar:
            st.markdown("---")
            if st.session_state.authenticated:
                athlete_name = st.session_state.strava_token.get('athlete_name', 'User')
                st.markdown(f"👤 Logged in as **{athlete_name}**")
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.strava_token = None
                    st.rerun()
    
    def run(self) -> None:
        """Run the application."""
        # Check authentication first
        if not self._check_authentication():
            return
        
        st.title("🏃 Strava Running Analytics")
        st.markdown("Interactive dashboard for your Strava activities")
        
        # Show logout button
        self._show_logout_button()
        
        # Load data
        df = self.load_data()
        
        # Initialize analyzer
        analyzer = RunningAnalyzer(df)
        analyzer.prepare_dataframe()
        
        # Filter to runs only
        runs_df = analyzer.runs_df
        
        # Sidebar Filters
        st.sidebar.header("📊 Filters")
        
        # Date range filter
        min_date = runs_df['date'].min()
        max_date = runs_df['date'].max()
        date_range = st.sidebar.date_input(
            "Select Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        
        if len(date_range) == 2:
            filtered_runs = analyzer.filter_by_date_range(date_range[0], date_range[1])
        else:
            filtered_runs = runs_df
        
        # Day of week filter
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        selected_days = st.sidebar.multiselect(
            "Select Days of Week:",
            options=days_order,
            default=days_order,
        )
        
        filtered_runs = filtered_runs[filtered_runs['day_of_week'].isin(selected_days)]
        
        # Distance range filter
        min_dist = float(runs_df['distance_miles'].min())
        max_dist = float(runs_df['distance_miles'].max())
        dist_range = st.sidebar.slider(
            "Distance Range (miles):",
            min_value=min_dist,
            max_value=max_dist,
            value=(min_dist, max_dist),
            step=0.5
        )
        
        filtered_runs = filtered_runs[
            (filtered_runs['distance_miles'] >= dist_range[0]) &
            (filtered_runs['distance_miles'] <= dist_range[1])
        ]
        
        # Main metrics
        st.header("📈 Summary Statistics")
        
        # Calculate stats for filtered runs
        filtered_analyzer = RunningAnalyzer(
            pd.concat([filtered_runs, df[df['type'] != 'Run']])
        )
        filtered_stats = {
            'total_runs': len(filtered_runs),
            'total_distance': round(filtered_runs['distance_miles'].sum(), 2),
            'avg_distance': round(filtered_runs['distance_miles'].mean(), 2),
            'avg_heart_rate': round(
                filtered_runs['average_heartrate_bpm'].dropna().mean(), 0
            ),
            'max_distance': round(filtered_runs['distance_miles'].max(), 2),
            'min_distance': round(filtered_runs['distance_miles'].min(), 2),
            'max_heart_rate': round(
                filtered_runs['average_heartrate_bpm'].dropna().max(), 0
            ),
            'min_heart_rate': round(
                filtered_runs['average_heartrate_bpm'].dropna().min(), 0
            ),
            'total_activities': len(df),
        }
        
        MetricsComponent.display_summary_metrics(filtered_stats)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Distance Over Time",
            "🗓️ Runs by Day",
            "📋 Run Details",
            "📉 Statistics",
            "💬 Ask Perplexity"
        ])
        
        # Tab 1: Distance Over Time
        with tab1:
            st.subheader("Distance Over Time")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                time_grouping = st.selectbox(
                    "Group by:",
                    options=["Day", "Week", "Month"],
                    key="time_group"
                )
            
            ChartsComponent.distance_over_time(filtered_runs, time_grouping)
        
        # Tab 2: Runs by Day of Week
        with tab2:
            st.subheader("Analysis by Day of Week")
            
            day_stats = analyzer.get_daily_stats()
            
            ChartsComponent.runs_by_day(day_stats)
            
            st.subheader("Day of Week Statistics")
            st.dataframe(
                day_stats.round(2),
                width='stretch',
                hide_index=True
            )
        
        # Tab 3: Run Details
        with tab3:
            st.subheader("Detailed Run Information")
            
            display_cols = [
                'date', 'day_abbr', 'distance_miles', 'moving_time',
                'pace_min_per_mile', 'average_heartrate_bpm',
                'elevation_high_ft', 'elevation_low_ft'
            ]
            
            display_df = filtered_runs[display_cols].copy()
            display_df.columns = [
                'Date', 'Day', 'Distance (mi)', 'Time', 'Pace',
                'Avg HR', 'Elev High (ft)', 'Elev Low (ft)'
            ]
            display_df = display_df.sort_values('Date', ascending=False)
            
            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"runs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # Tab 4: Statistics
        with tab4:
            st.subheader("Running Statistics")
            
            MetricsComponent.display_statistics_cards(filtered_stats)
            
            st.markdown("### Distance Distribution")
            ChartsComponent.distance_distribution(filtered_runs)
            
            st.markdown("### Heart Rate vs Distance")
            ChartsComponent.heart_rate_vs_distance(filtered_runs)
        
        # Tab 5: Ask Perplexity
        with tab5:
            # Create data context
            data_context = PerplexityClient.create_context(df, analyzer)
            AITabComponent.render(data_context)


def main():
    """Entry point for the application."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
