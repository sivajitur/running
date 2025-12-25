import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS format"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def load_activities_data(raw_activities):
    # Process raw activities data - filter only Run activities
    data = {}
    for activity in raw_activities:
        # Only include activities with type "Run"
        if activity.get('type') != 'Run':
            continue
            
        date_key = activity['start_date'][:10]  # YYYY-MM-DD
        data[date_key] = {
            'date': activity['start_date'],
            'distance': activity['distance'],
            'moving_time': activity['moving_time'],
            'elapsed_time': activity['elapsed_time'],
            'average_speed': activity['average_speed'],
            'max_speed': activity['max_speed'],
            'total_elevation_gain': activity.get('total_elevation_gain', 0)
        }
        if activity.get('has_heartrate'):
            data[date_key]['average_heartrate'] = activity['average_heartrate']
    
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index = pd.to_datetime(df.index)
    df['date'] = pd.to_datetime(df['date'])
    
    # Convert to American units
    df['Distance (mi)'] = df['distance'] / 1609.34
    df['Moving Time (sec)'] = df['moving_time'].apply(seconds_to_hms)
    df['Elapsed Time (sec)'] = df['elapsed_time'].apply(seconds_to_hms)
    df['Average Speed (mph)'] = df['average_speed'] * 2.23694  # m/s to mph
    df['Max Speed (mph)'] = df['max_speed'] * 2.23694
    df['Elevation Gain (ft)'] = df['total_elevation_gain'] * 3.28084  # meters to feet
    if 'average_heartrate' in df.columns:
        df['Average Heartrate (bpm)'] = df['average_heartrate']
    
    # Add weekday column
    df['Weekday'] = df.index.day_name()
    
    # Add pace column (minutes per mile)
    df['Pace (min/mi)'] = df['moving_time'] / (df['Distance (mi)'] * 60)
    
    # Keep only the converted columns and date
    columns_to_keep = ['date', 'Weekday', 'Distance (mi)', 'Moving Time (sec)', 'Elapsed Time (sec)', 
                      'Average Speed (mph)', 'Max Speed (mph)', 'Elevation Gain (ft)', 'Pace (min/mi)']
    if 'average_heartrate' in df.columns:
        columns_to_keep.append('Average Heartrate (bpm)')
    
    df = df[columns_to_keep]
    
    return df

def get_distance_over_time(df, weekday_filter=None):
    filtered_df = df
    if weekday_filter is not None:
        filtered_df = df[df.index.weekday == weekday_filter]
    return filtered_df[['date', 'Distance (mi)']].sort_values('date')

def get_heart_rate_data(df):
    hr_df = df.dropna(subset=['Average Heartrate (bpm)'])
    return hr_df['Average Heartrate (bpm)']

def get_elevation_data(df):
    elev_df = df.dropna(subset=['Elevation Gain (ft)'])
    return elev_df['Elevation Gain (ft)']

# Example usage
if __name__ == "__main__":
    # This would need actual raw activities data
    # df = load_activities_data(raw_activities)
    print("Run from main app to use session data")
