"""Dashboard Page - Overview of forecasts, models, and system status"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional, Dict

from utils import (
    get_api_client,
    format_admission_value,
    calculate_admission_change
)


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


def render_dashboard_page(location: str, lookback_days: int):
    """
    Render the Dashboard page with system status and latest forecasts.

    Args:
        location: Selected location from sidebar
        lookback_days: Default lookback days from sidebar
    """
    st.title("📊 Flu Forecasting Dashboard")
    st.markdown("Overview of current forecasts, models, and system status")

    # Header metrics
    st.subheader("System Status")

    # Fetch health data
    api_client = get_api_client()
    health_data = fetch_from_api("/api/v1/health", api_client)
    data_freshness = fetch_from_api("/api/v1/data/freshness", api_client)

    if health_data and data_freshness:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            api_status = health_data.get("status", "unknown")
            st.metric(
                "API Status",
                "🟢 Operational" if api_status == "operational" else "🔴 Down",
                delta=health_data.get("version", "")
            )

        with col2:
            db_status = health_data.get("components", {}).get("database", "unknown")
            st.metric(
                "Database",
                "🟢 Connected" if "healthy" in str(db_status).lower() else "🔴 Error"
            )

        with col3:
            sources = data_freshness.get("sources", [])
            fresh_count = sum(1 for s in sources if s.get("status") == "fresh")
            total_count = len(sources)
            st.metric(
                "Data Freshness",
                f"{fresh_count}/{total_count} Fresh",
                delta=f"{int(100*fresh_count/total_count if total_count else 0)}%"
            )

        with col4:
            uptime = health_data.get("uptime_seconds", 0)
            hours = uptime // 3600
            st.metric(
                "Uptime",
                f"{hours}h" if hours > 0 else "< 1h"
            )

    st.markdown("---")

    # Hospital Admissions (Primary Forecast Target)
    st.subheader(f"Hospital Admissions - {location}")

    surveillance_data = fetch_from_api(f"/api/v1/surveillance/current?location={location}&limit=7", api_client)

    if surveillance_data and surveillance_data.get("records"):
        surveillance = surveillance_data["records"]
        if len(surveillance) > 0:
            latest_admission = surveillance[0]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Latest Admissions",
                    format_admission_value(latest_admission.get("hospital_admissions", 0))
                )

            with col2:
                epiweek = latest_admission.get("epiweek", "N/A")
                st.metric(
                    "Epiweek",
                    str(epiweek)
                )

            with col3:
                # Calculate change from previous period if available
                if len(surveillance) > 1:
                    current = latest_admission.get("hospital_admissions", 0)
                    previous = surveillance[1].get("hospital_admissions", 0)
                    pct_change, direction = calculate_admission_change(current, previous)
                    st.metric(
                        "Change",
                        f"{direction} {pct_change:.1f}%"
                    )
    else:
        st.info("📭 No admission data available")

    st.markdown("---")

    # Latest forecast
    st.subheader(f"Latest Forecast - {location}")

    forecast_data = fetch_from_api(f"/api/v1/forecasts/latest?location={location}&limit=1", api_client)

    if forecast_data and forecast_data.get("forecasts"):
        forecast = forecast_data["forecasts"][0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Forecast Date", forecast.get("forecast_date", "N/A"))
        with col2:
            st.metric("Predicted Value", f"{forecast.get('value', 0):.0f}")
        with col3:
            lower = float(forecast.get("lower_bound") or 0)
            upper = float(forecast.get("upper_bound") or 0)
            st.metric("Confidence Range", f"{lower:.0f} - {upper:.0f}")
        with col4:
            st.metric("Model", forecast.get("model_ensemble", "ensemble"))
    else:
        st.info("📭 No forecasts available yet")

    st.markdown("---")

    # Pipeline Summary
    st.subheader("Pipeline Status")

    pipeline_summary = fetch_from_api("/api/v1/data/summary", api_client)

    if pipeline_summary:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            forecasts_info = pipeline_summary.get("forecasts", {})
            st.metric(
                "Forecasts Generated",
                forecasts_info.get("total_generated", 0)
            )

        with col2:
            data_quality_info = pipeline_summary.get("data_quality", {})
            st.metric(
                "Data Completeness",
                f"{data_quality_info.get('completeness_percent', 0):.1f}%"
            )

        with col3:
            models_info = pipeline_summary.get("models", {})
            st.metric(
                "Active Models",
                models_info.get("active_models", 0)
            )

        with col4:
            data_sources_info = pipeline_summary.get("data_sources", {})
            healthy = data_sources_info.get("healthy", 0)
            total = data_sources_info.get("total", 0)
            st.metric(
                "Data Sources",
                f"{healthy}/{total} Healthy"
            )

    st.markdown("---")

    # Quick charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Model Performance Trend")
        # Create sample data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=12, freq='W')
        mae_values = np.random.uniform(5, 15, 12)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=mae_values,
            mode='lines+markers',
            name='MAE',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title="Weekly MAE (Mean Absolute Error)",
            xaxis_title="Date",
            yaxis_title="MAE",
            hovermode='x unified',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Data Source Status")

        if data_freshness:
            sources = data_freshness.get("sources", [])
            status_counts = {}
            for source in sources:
                status = source.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            if status_counts:
                fig = go.Figure(data=[go.Pie(
                    labels=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    marker=dict(colors=['#2ecc71', '#f39c12', '#e74c3c'])
                )])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Loading data sources...")
