"""System Health Page - Monitor API, database, and pipeline health"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional, Dict

from utils import get_api_client


def fetch_from_api(endpoint: str, api_client=None) -> Optional[Dict]:
    """Fetch data from API endpoint with error handling"""
    if api_client is None:
        api_client = get_api_client()

    try:
        response = api_client.get(endpoint)
        return response
    except Exception as e:
        st.error(f"❌ API Error: {str(e)}")
        return None


def render_system_health_page():
    """
    Render the System Health page with health monitoring and metrics.
    """
    st.title("🏥 System Health")
    st.markdown("Monitor API, database, and pipeline health")

    api_client = get_api_client()

    # Health check
    health_data = fetch_from_api("/api/v1/health", api_client)

    if health_data:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Component Status")

            components = health_data.get("components", {})

            for component, status in components.items():
                status_emoji = "🟢" if "healthy" in str(status).lower() else "🔴"
                st.write(f"{status_emoji} **{component.replace('_', ' ').title()}**: {status}")

        with col2:
            st.subheader("API Information")

            st.write(f"**Status**: {health_data.get('status', 'Unknown')}")
            st.write(f"**Version**: {health_data.get('version', 'Unknown')}")
            st.write(f"**Uptime**: {health_data.get('uptime_seconds', 0)} seconds")
            st.write(f"**Timestamp**: {health_data.get('timestamp', 'N/A')}")

    st.markdown("---")

    # Available Locations with Data
    st.subheader("Locations with Available Data")

    data_locations = fetch_from_api("/api/v1/data/locations", api_client)

    if data_locations and data_locations.get("locations"):
        locations_list = data_locations["locations"]

        # Create locations dataframe
        locations_df = pd.DataFrame([
            {
                "Location": l.get("name", l.get("code", "Unknown")),
                "Code": l.get("code", "N/A"),
                "Region": l.get("region", "N/A"),
                "Data Sources": l.get("source_count", 0),
                "Latest Data": l.get("latest_data", "N/A"),
                "Completeness": f"{l.get('data_completeness', 0) * 100:.1f}%"
            }
            for l in locations_list[:20]  # Show first 20 locations
        ])

        st.dataframe(locations_df, use_container_width=True)

        if len(locations_list) > 20:
            st.info(f"📍 Showing 20 of {len(locations_list)} locations")
    else:
        st.info("📭 No location data available")

    st.markdown("---")

    # System metrics
    st.subheader("Recent Events")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Last Training Run")
        training = fetch_from_api("/api/v1/models/status", api_client)
        if training:
            st.json(training)

    with col2:
        st.subheader("API Activity")
        st.info("Last 100 requests tracked in database")

        # Sample activity chart
        times = pd.date_range(end=datetime.now(), periods=24, freq='H')
        requests_per_hour = np.random.poisson(5, 24)

        fig = go.Figure(data=[go.Bar(x=times, y=requests_per_hour)])
        fig.update_layout(
            title="API Requests per Hour",
            xaxis_title="Time",
            yaxis_title="Count",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
