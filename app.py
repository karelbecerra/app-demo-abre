"""
Flu Forecasting Pipeline - Web Dashboard

Interactive Streamlit dashboard for:
- Forecast visualization and comparison
- Model performance tracking
- System health monitoring
- Data quality analysis
"""

import streamlit as st
from datetime import datetime
import logging

# Local imports
from pages.dashboard import render_dashboard_page
from pages.data_analysis import render_data_analysis_page
from pages.forecasts import render_forecasts_page
from pages.models import render_models_page
from pages.data_quality import render_data_quality_page
from pages.system_health import render_system_health_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Flu Forecasting Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure API base URL
API_BASE_URL = "http://localhost:8000"


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

with st.sidebar:
    st.title("🦠 Flu Forecast")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Data Analysis",
            "Forecasts",
            "Models",
            "Data Quality",
            "System Health"
        ]
    )

    st.markdown("---")

    # Settings
    st.subheader("⚙️ Settings")
    location = st.selectbox(
        "Location",
        ["US", "hhs1", "hhs2", "hhs3", "hhs4", "hhs5", "hhs6", "hhs7", "hhs8", "hhs9", "hhs10"],
        index=0
    )

    horizon = st.slider(
        "Forecast Horizon (weeks)",
        min_value=1,
        max_value=8,
        value=4
    )

    lookback_days = st.slider(
        "Historical Data (days)",
        min_value=7,
        max_value=365,
        value=90
    )

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if page == "Dashboard":
    render_dashboard_page(location, lookback_days)

# ============================================================================
# PAGE: DATA ANALYSIS
# ============================================================================

elif page == "Data Analysis":
    render_data_analysis_page(location, lookback_days)

# ============================================================================
# PAGE: FORECASTS
# ============================================================================

elif page == "Forecasts":
    render_forecasts_page(location, horizon, API_BASE_URL)

# ============================================================================
# PAGE: MODELS
# ============================================================================

elif page == "Models":
    render_models_page(location, horizon)

# ============================================================================
# PAGE: DATA QUALITY
# ============================================================================

elif page == "Data Quality":
    render_data_quality_page()

# ============================================================================
# PAGE: SYSTEM HEALTH
# ============================================================================

elif page == "System Health":
    render_system_health_page()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<p>Flu Forecasting Pipeline • Phase 6.3 • Built with Streamlit</p>
<p><small>Data updated automatically from REST API</small></p>
</div>
""", unsafe_allow_html=True)
