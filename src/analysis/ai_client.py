"""
Perplexity AI client for running insights.
"""

import requests
from typing import Optional
from ..config import Settings


class PerplexityClient:
    """Client for querying Perplexity AI API."""
    
    def __init__(self):
        """Initialize Perplexity client."""
        self.api_key = Settings.PERPLEXITY_API_KEY
        self.api_url = Settings.PERPLEXITY_API_URL
        self.model = Settings.PERPLEXITY_MODEL
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and self.api_key != "your_perplexity_api_key")
    
    def query(self, question: str, context: str) -> str:
        """
        Query Perplexity API with context.
        
        Args:
            question: User question
            context: Data context to include
            
        Returns:
            str: AI response or error message
        """
        if not self.is_configured():
            return (
                "⚠️ Perplexity API key not configured. "
                "Please add PERPLEXITY_API_KEY to your .env file."
            )
        
        system_message = f"""You are a helpful running coach assistant. 
You have access to the user's Strava running data. 
Use this context to provide personalized insights and advice.

User's Running Data Context:
{context}
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": question},
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "return_citations": True,
            "search_recency_filter": "month"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "No response received from Perplexity API"
        
        except requests.exceptions.Timeout:
            return "Error: Request to Perplexity API timed out. Please try again."
        except requests.exceptions.HTTPError as e:
            return f"Error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Error querying Perplexity: {str(e)}"
    
    @staticmethod
    def create_context(df, analyzer) -> str:
        """
        Create a context string from running data.
        
        Args:
            df: Full activity DataFrame
            analyzer: RunningAnalyzer instance
            
        Returns:
            str: Formatted context for AI
        """
        runs_df = df[df['type'] == 'Run'].copy()
        stats = analyzer.get_summary_stats()
        
        context = f"""
## Running Activity Summary

**Data Period:** {df['date'].min().date()} to {df['date'].max().date()}

**Total Activities:** {stats['total_activities']} ({stats['total_runs']} runs)

**Distance Statistics (miles):**
- Total: {stats['total_distance']}
- Average: {stats['avg_distance']}
- Max: {stats['max_distance']}
- Min: {stats['min_distance']}

**Heart Rate Statistics (bpm):**
- Average: {stats['avg_heart_rate']}
- Max: {stats['max_heart_rate']}
- Min: {stats['min_heart_rate']}

**Elevation Statistics (feet):**
- Highest Elevation: {runs_df['elevation_high_ft'].max():.0f}
- Average High Elevation: {runs_df['elevation_high_ft'].mean():.0f}

**Activity Breakdown:**
{df['type'].value_counts().to_string()}

**Recent Activities:**
{runs_df.head(10)[['date', 'distance_miles', 'moving_time', 'average_heartrate_bpm']].to_string()}
"""
        return context
