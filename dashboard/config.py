"""
Dashboard Configuration

Settings for Streamlit dashboard including API endpoints, cache settings, etc.
"""

import os
from typing import List, Dict

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

# Dashboard Configuration
DASHBOARD_TITLE = "Flu Forecasting Pipeline Dashboard"
DASHBOARD_ICON = "🦠"
DASHBOARD_LAYOUT = "wide"

# Available Locations
LOCATIONS = [
    "US",
    "hhs1", "hhs2", "hhs3", "hhs4", "hhs5",
    "hhs6", "hhs7", "hhs8", "hhs9", "hhs10"
]

# Available Models
MODELS = [
    "baseline",
    "arima",
    "prophet",
    "xgboost",
    "lightgbm",
    "ensemble"
]

# Data Sources (7 total)
DATA_SOURCES = [
    "Hospital Admissions",
    "ILINet",
    "Clinical Lab",
    "FluSurv-NET",
    "Mortality Data",
    "State Activity",
    "FluSight Targets"
]

# Chart Colors
COLORS = {
    "fresh": "#2ecc71",      # Green
    "stale": "#f39c12",      # Orange
    "missing": "#e74c3c",    # Red
    "primary": "#1f77b4",    # Blue
    "secondary": "#ff7f0e"   # Orange
}

# Page Configuration
PAGES = [
    "Dashboard",
    "Data Analysis",
    "Forecasts",
    "Models",
    "Data Quality",
    "System Health"
]

# Cache Configuration
CACHE_TTL = 300  # 5 minutes

# Default Parameters
DEFAULT_LOCATION = "US"
DEFAULT_HORIZON = 4
DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_LIMIT = 10

# Refresh Settings
AUTO_REFRESH = os.getenv("AUTO_REFRESH", "false").lower() == "true"
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "300"))  # 5 minutes

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

print(f"""
Dashboard Configuration:
- API Base URL: {API_BASE_URL}
- Locations: {len(LOCATIONS)} available
- Models: {len(MODELS)} available
- Data Sources: {len(DATA_SOURCES)} available
""")
