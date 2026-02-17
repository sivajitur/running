"""
Data processing and transformation utilities.
"""

import json
import os
import pandas as pd
from typing import List, Dict, Any
from ..config import Settings


class DataProcessor:
    """Process and transform Strava activity data."""
    
    @staticmethod
    def seconds_to_hms(seconds: int) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def meters_to_miles(meters: float) -> float:
        """Convert meters to miles."""
        return meters / 1609.34
    
    @staticmethod
    def meters_to_feet(meters: float) -> float:
        """Convert meters to feet."""
        return meters * 3.28084
    
    @staticmethod
    def avg_speed_to_pace(avg_speed_ms: float, distance_m: float) -> float:
        """
        Calculate pace (minutes per mile) from average speed.
        
        Args:
            avg_speed_ms: Average speed in meters per second
            distance_m: Distance in meters
            
        Returns:
            float: Pace in minutes per mile
        """
        if avg_speed_ms == 0 or distance_m == 0:
            return 0
        
        distance_miles = DataProcessor.meters_to_miles(distance_m)
        time_seconds = distance_m / avg_speed_ms
        time_minutes = time_seconds / 60
        pace = time_minutes / distance_miles
        
        return pace
    
    @staticmethod
    def pace_to_hms(pace_min_per_mile: float) -> str:
        """Convert pace (minutes per mile) to MM:SS format."""
        if pace_min_per_mile == 0:
            return "00:00"
        
        total_seconds = int(pace_min_per_mile * 60)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @classmethod
    def convert_activities_to_dataframe(cls, activities: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert raw Strava activities to a structured DataFrame.
        
        Args:
            activities: List of raw activity dictionaries from Strava API
            
        Returns:
            pd.DataFrame: Processed activities with converted units and calculated fields
        """
        records = []
        
        for activity in activities:
            try:
                # Parse date - keep as datetime
                date_str = activity.get("start_date_local", "")
                date = pd.to_datetime(date_str.replace("Z", "+00:00"))
                
                # Get type
                activity_type = activity.get("type", "Unknown")
                
                # Convert distance to miles
                distance_miles = cls.meters_to_miles(activity.get("distance", 0))
                
                # Convert moving time to HH:MM:SS
                moving_time_hms = cls.seconds_to_hms(activity.get("moving_time", 0))
                
                # Calculate pace (minutes per mile)
                avg_speed_ms = activity.get("average_speed", 0)
                distance_m = activity.get("distance", 0)
                pace = cls.avg_speed_to_pace(avg_speed_ms, distance_m)
                pace_hms = cls.pace_to_hms(pace)
                
                # Get heart rate
                avg_hr = activity.get("average_heartrate", None)
                
                # Convert elevation to feet
                elev_high_ft = cls.meters_to_feet(activity.get("elev_high", 0))
                elev_low_ft = cls.meters_to_feet(activity.get("elev_low", 0))
                
                record = {
                    "date": date,
                    "type": activity_type,
                    "distance_miles": round(distance_miles, 2),
                    "moving_time": moving_time_hms,
                    "pace_min_per_mile": pace_hms,
                    "average_heartrate_bpm": avg_hr,
                    "elevation_high_ft": round(elev_high_ft, 1),
                    "elevation_low_ft": round(elev_low_ft, 1),
                }
                
                records.append(record)
            
            except Exception as e:
                print(f"Error processing activity: {e}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Sort by date (most recent first)
        df = df.sort_values("date", ascending=False).reset_index(drop=True)
        
        return df
    
    @staticmethod
    def load_csv(filepath: str = Settings.CSV_FILE) -> pd.DataFrame:
        """
        Load activities from CSV file.
        If file doesn't exist, returns empty DataFrame.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            pd.DataFrame: Activities with proper data types, or empty DataFrame if file not found
        """
        import os
        
        # Check if file exists
        if not os.path.exists(filepath):
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'date', 'type', 'distance_miles', 'moving_time',
                'pace_min_per_mile', 'average_heartrate_bpm',
                'elevation_high_ft', 'elevation_low_ft'
            ])
        
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    @staticmethod
    def save_csv(df: pd.DataFrame, filepath: str = Settings.CSV_FILE) -> None:
        """
        Save activities to CSV file.
        
        Args:
            df: DataFrame to save
            filepath: Path to save CSV file
        """
        df.to_csv(filepath, index=False)
    
    @staticmethod
    def save_json(activities: List[Dict[str, Any]], filepath: str = Settings.JSON_FILE) -> None:
        """
        Save raw activities to JSON file.
        
        Args:
            activities: List of activity dictionaries
            filepath: Path to save JSON file
        """
        with open(filepath, "w") as f:
            json.dump(activities, f, indent=2, default=str)
