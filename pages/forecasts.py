"""Forecasts Page - View and analyze forecasts for different locations and horizons"""

import streamlit as st
import pandas as pd
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


def render_forecasts_page(location: str, horizon: int, api_base_url: str = "http://localhost:8000"):
    """
    Render the Forecasts page with forecast analysis and comparison.

    Args:
        location: Selected location from sidebar
        horizon: Selected forecast horizon from sidebar
        api_base_url: Base URL for API endpoints
    """
    st.title("📈 Forecasts")
    st.markdown("View and analyze forecasts for different locations and horizons")

    # Export Tab
    st.markdown("**💾 Quick Export:**")
    col_export1, col_export2, col_export3, col_export4 = st.columns(4)

    api_client = get_api_client()

    with col_export1:
        export_location = st.selectbox(
            "Location",
            ["US", "hhs1", "hhs2", "hhs3", "hhs4", "hhs5", "hhs6", "hhs7", "hhs8", "hhs9", "hhs10"],
            key="export_location"
        )

    with col_export2:
        export_horizon = st.slider(
            "Horizon",
            min_value=1,
            max_value=8,
            value=4,
            key="export_horizon"
        )

    with col_export3:
        export_days = st.number_input(
            "Days",
            min_value=1,
            max_value=365,
            value=90,
            key="export_days"
        )

    with col_export4:
        if st.button("📥 Download CSV", key="export_button"):
            # Attempt to fetch and trigger CSV download
            csv_url = f"/api/v1/forecasts/export/{export_location}/{export_horizon}?days={export_days}"
            st.info(f"📥 To export: Visit API endpoint or use: `curl '{api_base_url}{csv_url}' -o forecasts.csv`")

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        comparison_location = st.selectbox(
            "Select Location",
            ["US", "hhs1", "hhs2", "hhs3", "hhs4", "hhs5", "hhs6", "hhs7", "hhs8", "hhs9", "hhs10"],
            key="forecast_location"
        )
    with col2:
        comparison_horizon = st.slider(
            "Horizon",
            min_value=1,
            max_value=8,
            value=4,
            key="forecast_horizon"
        )
    with col3:
        limit = st.slider(
            "Number of Forecasts",
            min_value=5,
            max_value=50,
            value=10,
            key="forecast_limit"
        )

    # Fetch latest forecast data
    forecast_data = fetch_from_api(
        f"/api/v1/forecasts/latest?location={comparison_location}&horizon={comparison_horizon}&limit={limit}",
        api_client
    )

    # Also fetch forecast comparison (how forecasts change over time)
    comparison_data = fetch_from_api(
        f"/api/v1/forecasts/compare/{comparison_location}/{comparison_horizon}?days=90",
        api_client
    )

    if forecast_data and forecast_data.get("forecasts"):
        forecasts = forecast_data["forecasts"]

        # Convert to DataFrame
        df = pd.DataFrame(forecasts)

        # Display table
        st.subheader(f"Forecasts for {comparison_location}")
        st.dataframe(
            df[["forecast_date", "horizon", "value", "lower_bound", "upper_bound", "model_ensemble"]],
            use_container_width=True
        )

        # Chart
        st.subheader("Forecast Values Over Time")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["forecast_date"], y=df["value"],
            mode='lines+markers',
            name='Prediction',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df["forecast_date"], y=df["upper_bound"],
            fill=None,
            mode='lines',
            name='Upper Bound',
            line=dict(width=0),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df["forecast_date"], y=df["lower_bound"],
            fill='tonexty',
            mode='lines',
            name='Confidence Interval',
            line=dict(width=0)
        ))

        fig.update_layout(
            title=f"Forecast Predictions - {comparison_location}",
            xaxis_title="Forecast Date",
            yaxis_title="Hospital Admissions",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 No forecasts available")

    st.markdown("---")

    # Forecast Comparison Over Time
    st.subheader("Forecast Model Comparison Over Time")

    if comparison_data and comparison_data.get("comparison"):
        comparison_array = comparison_data["comparison"]

        # Convert comparison data to dataframe for visualization
        if comparison_array and isinstance(comparison_array, list) and len(comparison_array) > 0:
            dates = []
            ensemble_values = []

            for item in comparison_array:
                if isinstance(item, dict):
                    dates.append(item.get("forecast_date", item.get("date")))
                    ensemble_values.append(item.get("ensemble_value", item.get("value")))

            if dates and ensemble_values:
                fig = go.Figure()

                # Extract individual model forecasts if available
                if comparison_array and isinstance(comparison_array[0], dict) and "models" in comparison_array[0]:
                    # Add each model's forecast line
                    models_dict = comparison_array[0].get("models", {})
                    for model_name in models_dict.keys():
                        model_values = [item.get("models", {}).get(model_name) for item in comparison_array]
                        fig.add_trace(go.Scatter(
                            x=dates, y=model_values,
                            mode='lines', name=model_name.title(),
                            opacity=0.7
                        ))

                # Add ensemble forecast as bold line
                fig.add_trace(go.Scatter(
                    x=dates, y=ensemble_values,
                    mode='lines+markers', name='Ensemble',
                    line=dict(width=3, color='#9467bd'),
                    marker=dict(size=8)
                ))

                fig.update_layout(
                    title=f"Forecast Predictions Over Time - {comparison_location} (Horizon: {comparison_horizon}w)",
                    xaxis_title="Forecast Issue Date",
                    yaxis_title="Predicted Hospital Admissions",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No model comparison data available")
        else:
            st.info("No comparison data available")
    else:
        st.info("📭 Forecast comparison data not available")
