"""Data Analysis Page - Interactive visualization of surveillance data"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from utils import get_api_client, convert_epiweek_to_date


def render_data_analysis_page(location: str, lookback_days: int):
    """
    Render the Data Analysis page with surveillance data visualization.

    Args:
        location: Selected location from sidebar
        lookback_days: Default lookback days from sidebar
    """
    st.title("📊 Data Analysis")
    ##st.markdown("Interactive visualization of surveillance data: forecast and merged data")

    # Create a container for results that will appear at the top
    results_container = st.container()

    ##st.markdown("---")

    # Filter Section (moved to bottom)
    ##st.subheader("🎛️ Filters")

    # Row 1: Month and Year selection
    col1, col2 = st.columns(2)

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    years = list(range(2020, 2027))

    # Get default date from lookback_days
    default_date = datetime.now() - timedelta(days=lookback_days)
    default_month = default_date.month - 1  # Convert to 0-indexed
    default_year = default_date.year

    with col1:
        selected_month = st.selectbox(
            "Historical data starting from",
            options=range(12),
            format_func=lambda x: months[x],
            index=default_month,
            key="data_analysis_month"
        )

    with col2:
        selected_year = st.selectbox(
            "Year",
            options=years,
            index=years.index(default_year) if default_year in years else 0,
            key="data_analysis_year"
        )

    # Convert month/year to start_date
    start_date = datetime(selected_year, selected_month + 1, 1)

    # Data Columns (hidden from UI, always use hospital_admissions)
    available_columns = [
        "hospital_admissions",
        "ili_wili",
        "ili_ili",
        "lab_percent_positive",
        "lab_total_specimens",
        "target_weekly_rate"
    ]

    column_display_names = {
        "hospital_admissions": "Hospital Admissions",
        "ili_wili": "ILI Weighted (ILINet)",
        "ili_ili": "ILI Percentage (ILINet)",
        "lab_percent_positive": "Lab Positivity Rate (%)",
        "lab_total_specimens": "Lab Specimens Tested",
        "target_weekly_rate": "Target Weekly Rate"
    }

    # Use hospital_admissions by default (hidden from UI)
    selected_columns = ["hospital_admissions"]

    # Use only the primary location from sidebar
    all_locations = [location]

    # Data loading and visualization in results container (auto-load on filter change)
    # Validate inputs
    if not selected_columns:
        with results_container:
            st.error("❌ Please select at least one data column to visualize")
    else:
        # Show loading spinner
        with st.spinner("Loading data..."):
            # Fetch data from API
            api_client = get_api_client()
            all_traces = []
            first_forecast_date = None

            # Data sources: Forecast and Merged (always-on)
            sources_to_fetch = [
                ("forecast", "/api/v1/surveillance/forecasts"),
                ("historical", "/api/v1/surveillance/merged")
            ]

            # Fetch data for each combination
            for source_name, endpoint in sources_to_fetch:
                for loc in all_locations:
                    # Build params
                    params = {
                        "location": loc,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "limit": 10000
                    }

                    # Fetch data
                    try:
                        response = api_client.get(endpoint, params=params)

                        if response and response.get("records"):
                            records = response["records"]

                            # Process each selected column
                            for col in selected_columns:
                                # Extract dates and values
                                dates = []
                                values = []
                                lower_bounds = []
                                upper_bounds = []

                                for record in records:
                                    value = record.get(col)
                                    if value is not None:  # Skip null values
                                        # Convert epiweek to date
                                        epiweek = record.get("epiweek")
                                        date_str = convert_epiweek_to_date(epiweek)
                                        if date_str != "N/A":
                                            dates.append(date_str)
                                            values.append(value)

                                            # For forecast data, also collect bounds and track first forecast date
                                            if source_name == "forecast":
                                                lower_bounds.append(record.get("lower_bound"))
                                                upper_bounds.append(record.get("upper_bound"))
                                                # Capture first forecast date
                                                if first_forecast_date is None:
                                                    first_forecast_date = date_str

                                if dates and values:
                                    # For forecast data with bounds, create shaded ribbon
                                    if source_name == "forecast" and lower_bounds and upper_bounds:
                                        # Check if we have valid bounds
                                        if any(lb is not None for lb in lower_bounds) and any(ub is not None for ub in upper_bounds):
                                            # Add upper bound (invisible, for fill reference)
                                            all_traces.append(
                                                go.Scatter(
                                                    x=dates,
                                                    y=upper_bounds,
                                                    fill=None,
                                                    mode='lines',
                                                    name=f"{loc} - Upper Bound",
                                                    line=dict(width=0),
                                                    showlegend=False,
                                                    hoverinfo='skip'
                                                )
                                            )

                                            # Add lower bound with fill (creates the shaded area)
                                            all_traces.append(
                                                go.Scatter(
                                                    x=dates,
                                                    y=lower_bounds,
                                                    fill='tonexty',
                                                    mode='lines',
                                                    name=f"{loc} - Prediction Interval",
                                                    line=dict(width=0),
                                                    fillcolor="rgba(142, 215, 208, 0.9)",
                                                    hovertemplate='<b>Date:</b> %{x}<br><b>Range:</b> %{y:.0f}<extra></extra>'
                                                )
                                            )

                                    # Create main trace for values
                                    trace_name = f"{source_name.title()}"

                                    trace = go.Scatter(
                                        x=dates,
                                        y=values,
                                        mode='lines+markers',
                                        name=trace_name,
                                        line=dict(color='#636EFA', width=2),
                                        marker=dict(size=8, color='#636EFA', line=dict(color='white', width=1))
                                    )
                                    all_traces.append(trace)
                    except Exception as e:
                        st.warning(f"⚠️ Could not fetch {source_name} data for {loc}: {str(e)}")

            # Render chart in results container
            if all_traces:
                with results_container:
                    ##st.subheader("📈 Time Series Visualization")

                    fig = go.Figure(data=all_traces)

                    # Build shapes for vertical reference lines
                    shapes = []
                    annotations = []

                    # Add "Today" vertical line (light gray dashed)
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    shapes.append(
                        dict(
                            type="line",
                            x0=today_str,
                            x1=today_str,
                            y0=0,
                            y1=1,
                            yref="paper",
                            line=dict(color="lightgray", width=2, dash="dash")
                        )
                    )
                    annotations.append(
                        dict(
                            x=today_str,
                            y=1.05,
                            yref="paper",
                            text="<b>Today</b>",
                            showarrow=False,
                            font=dict(color="lightgray", size=10)
                        )
                    )

                    # Add "First Forecast Day" vertical line (gray dashed)
                    if first_forecast_date:
                        shapes.append(
                            dict(
                                type="line",
                                x0=first_forecast_date,
                                x1=first_forecast_date,
                                y0=0,
                                y1=1,
                                yref="paper",
                                line=dict(color="gray", width=2, dash="dash")
                            )
                        )
                        annotations.append(
                            dict(
                                x=first_forecast_date,
                                y=1.05,
                                yref="paper",
                                text="<b>First Forecast</b>",
                                showarrow=False,
                                font=dict(color="gray", size=10)
                            )
                        )

                    fig.update_layout(
                        title="Forecasted weekly influenza hospital admissions",
                        xaxis_title="Date",
                        yaxis_title="Incident weekly hospital admissions",
                        hovermode='x unified',
                        height=600,
                        xaxis=dict(
                            tickformat="%b %d %Y",
                            showline=True,
                            linewidth=2,
                            linecolor="darkgray"
                        ),
                        yaxis=dict(
                            tickformat=",.0f",
                            showline=True,
                            linewidth=2,
                            linecolor="darkgray"
                        ),
                        shapes=shapes,
                        annotations=annotations,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.25,
                            xanchor="center",
                            x=0.5,
                            bgcolor="rgba(255, 255, 255, 0.8)",
                            bordercolor="lightgray",
                            borderwidth=1
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

            else:
                with results_container:
                    st.warning("⚠️ No data available for the selected date range and columns")
