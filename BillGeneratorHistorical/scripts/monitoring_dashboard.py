"""
Monitoring dashboard for the Stream Bill Generator
This script provides a Streamlit dashboard for viewing performance metrics.
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def load_usage_logs(log_file: str = "logs/usage_log.json") -> list:
    """
    Load usage logs from file
    
    Args:
        log_file (str): Path to the usage log file
        
    Returns:
        list: List of log entries
    """
    logs = []
    if not os.path.exists(log_file):
        return logs
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception as e:
        st.error(f"Error loading logs: {e}")
        
    return logs

def parse_performance_logs(logs: list) -> pd.DataFrame:
    """
    Parse performance logs into a DataFrame
    
    Args:
        logs (list): List of log entries
        
    Returns:
        pd.DataFrame: DataFrame with performance data
    """
    performance_data = []
    
    for log in logs:
        if log.get("event") == "performance":
            context = log.get("context", {})
            performance_data.append({
                "timestamp": log.get("timestamp"),
                "operation": context.get("operation"),
                "duration": context.get("duration"),
                "file_size": context.get("details", {}).get("file_size", "N/A")
            })
    
    return pd.DataFrame(performance_data)

def parse_error_logs(logs: list) -> pd.DataFrame:
    """
    Parse error logs into a DataFrame
    
    Args:
        logs (list): List of log entries
        
    Returns:
        pd.DataFrame: DataFrame with error data
    """
    error_data = []
    
    for log in logs:
        if log.get("event") == "error":
            context = log.get("context", {})
            error_data.append({
                "timestamp": log.get("timestamp"),
                "error": context.get("error"),
                "details": str(context.get("details", {}))
            })
    
    return pd.DataFrame(error_data)

def create_performance_dashboard():
    """Create the performance monitoring dashboard"""
    st.set_page_config(
        page_title="Performance Monitoring Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Performance Monitoring Dashboard")
    st.markdown("Monitor application performance and usage metrics")
    
    # Load logs
    logs = load_usage_logs()
    
    if not logs:
        st.info("No usage logs found. Run the application to generate logs.")
        return
    
    # Parse logs
    performance_df = parse_performance_logs(logs)
    error_df = parse_error_logs(logs)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📈 Performance", "❌ Errors", "ℹ️ Overview"])
    
    with tab1:
        if not performance_df.empty:
            st.subheader("Performance Metrics")
            
            # Convert timestamp to datetime
            performance_df["timestamp"] = pd.to_datetime(performance_df["timestamp"])
            
            # Duration distribution
            fig_duration = px.histogram(
                performance_df, 
                x="duration", 
                nbins=20,
                title="Operation Duration Distribution"
            )
            st.plotly_chart(fig_duration, use_container_width=True)
            
            # Operations over time
            fig_timeline = px.line(
                performance_df,
                x="timestamp",
                y="duration",
                color="operation",
                title="Operation Performance Over Time"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Performance statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Operations", len(performance_df))
            with col2:
                avg_duration = performance_df["duration"].mean()
                st.metric("Average Duration (s)", f"{avg_duration:.2f}")
            with col3:
                max_duration = performance_df["duration"].max()
                st.metric("Max Duration (s)", f"{max_duration:.2f}")
            
            # Operation breakdown
            st.subheader("Operation Breakdown")
            operation_stats = performance_df.groupby("operation").agg({
                "duration": ["count", "mean", "min", "max"]
            }).round(2)
            operation_stats.columns = ["Count", "Avg Duration", "Min Duration", "Max Duration"]
            st.dataframe(operation_stats)
        else:
            st.info("No performance data available")
    
    with tab2:
        if not error_df.empty:
            st.subheader("Error Logs")
            
            # Convert timestamp to datetime
            error_df["timestamp"] = pd.to_datetime(error_df["timestamp"])
            
            # Error count over time
            error_df["date"] = error_df["timestamp"].dt.date
            error_count = error_df.groupby("date").size().reset_index(name="count")
            
            fig_errors = px.bar(
                error_count,
                x="date",
                y="count",
                title="Error Count Over Time"
            )
            st.plotly_chart(fig_errors, use_container_width=True)
            
            # Error details
            st.subheader("Recent Errors")
            st.dataframe(error_df[["timestamp", "error", "details"]].tail(20))
        else:
            st.info("No error data available")
    
    with tab3:
        st.subheader("Usage Overview")
        st.write(f"Total log entries: {len(logs)}")
        
        # Event type distribution
        event_types = {}
        for log in logs:
            event_type = log.get("event", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        if event_types:
            fig_events = px.pie(
                values=list(event_types.values()),
                names=list(event_types.keys()),
                title="Event Type Distribution"
            )
            st.plotly_chart(fig_events, use_container_width=True)
        
        # Recent activity
        st.subheader("Recent Activity")
        recent_logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]
        activity_data = []
        for log in recent_logs:
            activity_data.append({
                "timestamp": log.get("timestamp"),
                "event": log.get("event"),
                "summary": str(log.get("context", {}))[:100] + "..." if len(str(log.get("context", {}))) > 100 else str(log.get("context", {}))
            })
        
        st.dataframe(pd.DataFrame(activity_data))

def main():
    """Main function"""
    create_performance_dashboard()

if __name__ == "__main__":
    main()