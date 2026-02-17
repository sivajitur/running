"""
Running data analysis utilities.
"""

import pandas as pd
from typing import Dict, Any


class RunningAnalyzer:
    """Analyze running activities and provide statistics."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with activity data.
        
        Args:
            df: DataFrame with activity data
        """
        self.df = df
        self.runs_df = df[df['type'] == 'Run'].copy()
    
    def prepare_dataframe(self) -> None:
        """Add calculated columns to dataframe."""
        # Ensure date is datetime type
        self.runs_df['date'] = pd.to_datetime(self.runs_df['date'])
        
        self.runs_df['day_of_week'] = self.runs_df['date'].dt.day_name()
        self.runs_df['day_abbr'] = self.runs_df['date'].dt.strftime('%a')
        self.runs_df['week'] = self.runs_df['date'].dt.isocalendar().week
        self.runs_df['month'] = self.runs_df['date'].dt.strftime('%B')
        self.runs_df['year_month'] = self.runs_df['date'].dt.strftime('%Y-%m')
        self.runs_df['week_start'] = self.runs_df['date'] - pd.to_timedelta(
            self.runs_df['date'].dt.dayofweek, unit='d'
        )
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all activities."""
        return {
            "total_activities": len(self.df),
            "total_runs": len(self.runs_df),
            "total_distance": round(self.runs_df['distance_miles'].sum(), 2),
            "avg_distance": round(self.runs_df['distance_miles'].mean(), 2),
            "max_distance": round(self.runs_df['distance_miles'].max(), 2),
            "min_distance": round(self.runs_df['distance_miles'].min(), 2),
            "avg_heart_rate": round(
                self.runs_df['average_heartrate_bpm'].dropna().mean(), 0
            ),
            "max_heart_rate": round(
                self.runs_df['average_heartrate_bpm'].dropna().max(), 0
            ),
            "min_heart_rate": round(
                self.runs_df['average_heartrate_bpm'].dropna().min(), 0
            ),
        }
    
    def get_daily_stats(self) -> pd.DataFrame:
        """Get aggregated statistics by day of week."""
        day_stats = self.runs_df.groupby('day_abbr').agg({
            'distance_miles': ['count', 'sum', 'mean'],
            'average_heartrate_bpm': 'mean'
        }).reset_index()
        
        day_stats.columns = ['Day', 'Runs', 'Total Distance', 'Avg Distance', 'Avg HR']
        
        # Reorder by day of week
        day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_stats['Day'] = pd.Categorical(
            day_stats['Day'], categories=day_order, ordered=True
        )
        day_stats = day_stats.sort_values('Day')
        
        return day_stats
    
    def get_weekly_stats(self) -> pd.DataFrame:
        """Get aggregated statistics by week."""
        weekly_stats = self.runs_df.groupby('week_start').agg({
            'distance_miles': ['sum', 'count', 'mean'],
            'average_heartrate_bpm': 'mean'
        }).reset_index()
        
        weekly_stats.columns = [
            'Week Start', 'Total Distance', 'Runs', 'Avg Distance', 'Avg HR'
        ]
        
        return weekly_stats
    
    def get_monthly_stats(self) -> pd.DataFrame:
        """Get aggregated statistics by month."""
        monthly_stats = self.runs_df.groupby('year_month').agg({
            'distance_miles': ['sum', 'count', 'mean'],
            'average_heartrate_bpm': 'mean'
        }).reset_index()
        
        monthly_stats.columns = [
            'Month', 'Total Distance', 'Runs', 'Avg Distance', 'Avg HR'
        ]
        
        return monthly_stats
    
    def filter_by_days(self, days: list) -> pd.DataFrame:
        """
        Filter runs by day of week.
        
        Args:
            days: List of day names (e.g., ['Monday', 'Tuesday'])
            
        Returns:
            Filtered DataFrame
        """
        return self.runs_df[self.runs_df['day_of_week'].isin(days)]
    
    def filter_by_distance_range(
        self, min_distance: float, max_distance: float
    ) -> pd.DataFrame:
        """
        Filter runs by distance range.
        
        Args:
            min_distance: Minimum distance in miles
            max_distance: Maximum distance in miles
            
        Returns:
            Filtered DataFrame
        """
        return self.runs_df[
            (self.runs_df['distance_miles'] >= min_distance) &
            (self.runs_df['distance_miles'] <= max_distance)
        ]
    
    def filter_by_date_range(self, start_date, end_date) -> pd.DataFrame:
        """
        Filter runs by date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Filtered DataFrame
        """
        return self.runs_df[
            (self.runs_df['date'].dt.date >= start_date) &
            (self.runs_df['date'].dt.date <= end_date)
        ]
