"""
Metrics display components.
"""

import streamlit as st
from typing import Dict, Any


class MetricsComponent:
    """Display metric cards."""
    
    @staticmethod
    def display_summary_metrics(stats: Dict[str, Any]) -> None:
        """
        Display summary metric cards.
        
        Args:
            stats: Dictionary of statistics
        """
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Runs", stats['total_runs'])
        
        with col2:
            st.metric("Total Distance", f"{stats['total_distance']} mi")
        
        with col3:
            st.metric("Avg Distance", f"{stats['avg_distance']} mi")
        
        with col4:
            st.metric("Avg Heart Rate", f"{stats['avg_heart_rate']:.0f} bpm")
        
        with col5:
            st.metric("Longest Run", f"{stats['max_distance']} mi")
    
    @staticmethod
    def display_statistics_cards(stats: Dict[str, Any]) -> None:
        """
        Display detailed statistics cards.
        
        Args:
            stats: Dictionary of statistics
        """
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Distance Statistics")
            distance_stats = {
                'Min': stats['min_distance'],
                'Max': stats['max_distance'],
                'Mean': stats['avg_distance'],
            }
            for stat, value in distance_stats.items():
                st.metric(stat, f"{value:.2f} mi")
        
        with col2:
            st.markdown("### Heart Rate Statistics")
            hr_stats = {
                'Min': stats['min_heart_rate'],
                'Max': stats['max_heart_rate'],
                'Mean': stats['avg_heart_rate'],
            }
            for stat, value in hr_stats.items():
                st.metric(stat, f"{value:.0f} bpm")
