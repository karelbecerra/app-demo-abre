"""Models Page - Track model training, performance metrics, and comparisons"""

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


def render_models_page(location: str, horizon: int):
    """
    Render the Models page with model performance tracking and comparisons.

    Args:
        location: Selected location from sidebar
        horizon: Selected forecast horizon from sidebar
    """
    st.title("🤖 Model Performance")
    st.markdown("Track model training, performance metrics, and comparisons")

    api_client = get_api_client()

    # Model Status
    st.subheader("Training Status")
    model_status = fetch_from_api("/api/v1/models/status", api_client)

    if model_status:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Last Training", model_status.get("last_training_date", "Never"))
        with col2:
            st.metric("Status", model_status.get("status", "Unknown"))
        with col3:
            st.metric("Models Trained", len(model_status.get("models", [])))
        with col4:
            st.metric("Duration", f"{model_status.get('duration_seconds', 0)}s")

    st.markdown("---")

    # Performance History
    st.subheader("Performance Metrics Over Time")

    performance_data = fetch_from_api(f"/api/v1/models/performance?days=30&location={location}", api_client)

    if performance_data and performance_data.get("performance"):
        perf = performance_data["performance"]

        # Create sample performance chart
        metrics_df = pd.DataFrame({
            "date": pd.date_range(end=datetime.now(), periods=12, freq='W'),
            "mae": np.random.uniform(5, 15, 12),
            "rmse": np.random.uniform(10, 25, 12),
            "wis": np.random.uniform(100, 200, 12)
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=metrics_df["date"], y=metrics_df["mae"],
            mode='lines+markers', name='MAE'
        ))
        fig.add_trace(go.Scatter(
            x=metrics_df["date"], y=metrics_df["rmse"],
            mode='lines+markers', name='RMSE', yaxis='y2'
        ))

        fig.update_layout(
            title="Model Performance Metrics",
            xaxis_title="Date",
            yaxis_title="MAE",
            yaxis2=dict(title="RMSE", overlaying='y', side='right'),
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 No performance data available")

    st.markdown("---")

    # Model Comparison
    st.subheader("Model Comparison")

    comparison = fetch_from_api(f"/api/v1/models/comparison?location={location}&horizon={horizon}&days=30", api_client)

    if comparison:
        models_list = comparison.get("models", [])
        if models_list:
            comparison_df = pd.DataFrame(models_list)
            st.dataframe(comparison_df, use_container_width=True)
        else:
            st.info("No comparison data available")
