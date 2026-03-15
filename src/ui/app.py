"""
Main Streamlit application with Authentication.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time

from ..config import Settings
from ..data import DataProcessor, StravaClient
from ..data.database import init_db, upsert_activities, get_activity_count, load_all_activities
from ..analysis import RunningAnalyzer, ClaudeClient
from ..auth import StravaOAuthHandler, StravaToken
from .components import MetricsComponent, ChartsComponent, AITabComponent


class StreamlitApp:
    """Main Streamlit application."""

    def __init__(self):
        """Initialize the application."""
        self._setup_page()
        self._setup_session_state()
        init_db()

    def _setup_session_state(self) -> None:
        """Initialize session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'strava_token' not in st.session_state:
            st.session_state.strava_token = None
        if 'activities_df' not in st.session_state:
            st.session_state.activities_df = None

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

    def _load_data(self) -> pd.DataFrame:
        """
        Load activities for the current user.
        On first call: checks the local DB; if data exists, loads from there.
        If DB is empty (or a refresh was requested), fetches from Strava and
        persists to both SQLite (running.db) and JSON (strava_activities.json).
        """
        if st.session_state.activities_df is not None:
            return st.session_state.activities_df

        # Load from local DB when data already exists and no refresh requested
        if not st.session_state.get('force_refresh') and get_activity_count() > 0:
            with st.spinner("📂 Loading activities from local database..."):
                activities = load_all_activities()
                DataProcessor.save_json(activities)
                df = DataProcessor.convert_activities_to_dataframe(activities)
                st.session_state.activities_df = df
                return df

        # Otherwise fetch from Strava
        token_data = st.session_state.strava_token
        token = StravaToken.from_dict(token_data)

        # Refresh token if expired
        if token.is_expired():
            try:
                auth_handler = StravaOAuthHandler(
                    client_id=Settings.STRAVA_CLIENT_ID,
                    client_secret=Settings.STRAVA_CLIENT_SECRET,
                    redirect_uri=Settings.REDIRECT_URI,
                )
                token = auth_handler.refresh_access_token(token.refresh_token)
                st.session_state.strava_token = token.to_dict()
            except Exception:
                st.error("Your session has expired. Please log in again.")
                st.session_state.authenticated = False
                st.session_state.strava_token = None
                st.rerun()

        with st.spinner("📥 Fetching your activities from Strava..."):
            try:
                client = StravaClient(token.access_token)
                activities = client.get_activities(months_back=12)
                upsert_activities(activities)
                DataProcessor.save_json(activities)
                df = DataProcessor.convert_activities_to_dataframe(activities)
                st.session_state.activities_df = df
                st.session_state.force_refresh = False
                return df
            except Exception as e:
                st.error(f"❌ Failed to fetch activities: {str(e)}")
                st.stop()

    def _check_authentication(self) -> bool:
        """Check if user is authenticated."""
        if not st.session_state.authenticated:
            self._show_auth_page()
            return False
        return True

    def _show_auth_page(self) -> None:
        """Display the Strava login page."""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.image(
                "https://cdn2.strava.com/logo_files/strava_logo-1e6ce0ed2f3cc1f4eee8c8be12d7e2ba.svg",
                width=150
            )
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

            if not Settings.has_credentials():
                st.error(
                    "⚠️ This app is not configured yet. "
                    "Please contact the app owner to set up Strava credentials."
                )
                st.stop()

            auth_handler = StravaOAuthHandler(
                client_id=Settings.STRAVA_CLIENT_ID,
                client_secret=Settings.STRAVA_CLIENT_SECRET,
                redirect_uri=Settings.REDIRECT_URI,
            )

            auth_url = auth_handler.get_authorization_url()
            st.link_button(
                "🔗 Connect with Strava",
                url=auth_url,
                use_container_width=True,
                type="primary"
            )

            st.markdown("---")

            # Handle OAuth callback (auto-redirect with ?code=)
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

            # Fallback: manual code entry
            with st.expander("Having trouble? Enter authorization code manually"):
                manual_code = st.text_input(
                    "Paste your authorization code:",
                    placeholder="abc123xyz...",
                    type="password",
                    key="manual_auth_code"
                )
                if st.button("✅ Authenticate", use_container_width=True):
                    if not manual_code:
                        st.error("Please enter an authorization code")
                    else:
                        with st.spinner("Authenticating..."):
                            try:
                                token = auth_handler.exchange_code_for_token(manual_code)
                                st.session_state.strava_token = token.to_dict()
                                st.session_state.authenticated = True
                                st.success(f"✅ Welcome, {token.athlete_name}!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Authentication failed: {str(e)}")

        st.stop()

    def _show_logout_button(self) -> None:
        """Show logout and refresh buttons in sidebar."""
        with st.sidebar:
            st.markdown("---")
            if st.session_state.authenticated:
                athlete_name = st.session_state.strava_token.get('athlete_name', 'User')
                st.markdown(f"👤 Logged in as **{athlete_name}**")
                if st.button("🔄 Refresh from Strava", use_container_width=True):
                    st.session_state.activities_df = None
                    st.session_state.force_refresh = True
                    st.rerun()
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.strava_token = None
                    st.session_state.activities_df = None
                    st.session_state.force_refresh = False
                    st.rerun()

    def run(self) -> None:
        """Run the application."""
        if not self._check_authentication():
            return

        st.title("🏃 Strava Running Analytics")
        st.markdown("Interactive dashboard for your Strava activities")

        self._show_logout_button()

        df = self._load_data()

        analyzer = RunningAnalyzer(df)
        analyzer.prepare_dataframe()

        runs_df = analyzer.runs_df

        # Sidebar Filters
        st.sidebar.header("📊 Filters")

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

        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        selected_days = st.sidebar.multiselect(
            "Select Days of Week:",
            options=days_order,
            default=days_order,
        )

        filtered_runs = filtered_runs[filtered_runs['day_of_week'].isin(selected_days)]

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

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Distance Over Time",
            "🗓️ Runs by Day",
            "📋 Run Details",
            "📉 Statistics",
            "💬 Ask Claude"
        ])

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

        with tab2:
            st.subheader("Analysis by Day of Week")
            day_stats = analyzer.get_daily_stats()
            ChartsComponent.runs_by_day(day_stats)
            st.subheader("Day of Week Statistics")
            st.dataframe(day_stats.round(2), width='stretch', hide_index=True)

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
            st.dataframe(display_df, width='stretch', hide_index=True)
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"runs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with tab4:
            st.subheader("Running Statistics")
            MetricsComponent.display_statistics_cards(filtered_stats)
            st.markdown("### Distance Distribution")
            ChartsComponent.distance_distribution(filtered_runs)
            st.markdown("### Heart Rate vs Distance")
            ChartsComponent.heart_rate_vs_distance(filtered_runs)

        with tab5:
            data_context = ClaudeClient.create_context(df, analyzer)
            AITabComponent.render(data_context)


def main():
    """Entry point for the application."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
