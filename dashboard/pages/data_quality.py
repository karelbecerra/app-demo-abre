"""Data Quality Page - Monitor data freshness, completeness, and quality metrics"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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


def render_data_quality_page():
    """
    Render the Data Quality page with freshness, completeness, and quality metrics.
    """
    st.title("📊 Data Quality Analysis")
    st.markdown("Monitor data freshness, completeness, and quality metrics")

    api_client = get_api_client()

    # Data Freshness
    st.subheader("Data Freshness Status")

    freshness = fetch_from_api("/api/v1/data/freshness", api_client)

    if freshness and freshness.get("sources"):
        sources = freshness["sources"]

        # Create freshness dataframe
        freshness_df = pd.DataFrame([
            {
                "Source": s.get("name", "Unknown"),
                "Status": s.get("status", "unknown"),
                "Hours Old": s.get("hours_since_update", 0),
                "Records": s.get("record_count", 0)
            }
            for s in sources
        ])

        st.dataframe(freshness_df, use_container_width=True)

        # Status distribution
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Freshness Distribution")
            status_counts = freshness_df["Status"].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(colors=['#2ecc71', '#f39c12', '#e74c3c'])
            )])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Overall Quality Score")
            quality_score = freshness.get("overall_quality_score", 0)

            st.markdown(f"""
            <div style='text-align: center; font-size: 48px; font-weight: bold; color: #1f77b4;'>
            {quality_score:.1f}%
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No freshness data available")

    st.markdown("---")

    # Data Sources Information
    st.subheader("Configured Data Sources")

    data_sources = fetch_from_api("/api/v1/data/sources", api_client)

    if data_sources and data_sources.get("sources"):
        sources = data_sources["sources"]

        # Create sources dataframe
        sources_df = pd.DataFrame([
            {
                "Source": s.get("name", "Unknown"),
                "Description": s.get("description", "N/A")[:60] + "...",
                "Update Frequency": s.get("update_frequency", "N/A"),
                "Enabled": "✅" if s.get("enabled", False) else "❌"
            }
            for s in sources
        ])

        st.dataframe(sources_df, use_container_width=True)
    else:
        st.info("📭 No data sources information available")

    st.markdown("---")

    # Quality Report
    st.subheader("Data Quality Metrics")

    quality_report = fetch_from_api("/api/v1/data/quality-report", api_client)

    if quality_report:
        col1, col2, col3 = st.columns(3)

        completeness = quality_report.get("completeness", {})
        with col1:
            st.metric("Avg Completeness", f"{np.mean(list(completeness.values())):.1f}%")

        with col2:
            timeliness = quality_report.get("timeliness", {})
            st.metric("On Schedule", "✅ Yes" if timeliness.get("on_schedule") else "❌ No")

        with col3:
            overall = quality_report.get("overall_quality_score", 0)
            st.metric("Overall Score", f"{overall:.1f}%")
