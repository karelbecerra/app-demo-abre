"""
Dashboard Utilities

Helper functions for API calls, data processing, and formatting
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import streamlit as st

from config import API_BASE_URL, API_TIMEOUT, COLORS

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for API calls with error handling and caching"""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        GET request to API endpoint

        Args:
            endpoint: API endpoint path (e.g., "/api/v1/health")
            params: Query parameters

        Returns:
            JSON response or None if error
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to {endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None

    def post(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """
        POST request to API endpoint

        Args:
            endpoint: API endpoint path
            data: Request payload

        Returns:
            JSON response or None if error
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request error: {e}")
            return None


@st.cache_resource
def get_api_client() -> APIClient:
    """Get or create cached API client"""
    return APIClient()


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with proper decimals"""
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def format_date(date_str: str, format_str: str = "%Y-%m-%d") -> str:
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime(format_str)
    except:
        return date_str


def get_status_color(status: str) -> str:
    """Get color for status badge"""
    status_lower = status.lower()
    if status_lower == "fresh":
        return "🟢"
    elif status_lower == "stale":
        return "🟡"
    elif status_lower == "missing":
        return "🔴"
    else:
        return "⚪"


def get_status_badge(status: str) -> str:
    """Get HTML badge for status"""
    color = COLORS.get(status.lower(), COLORS.get("primary"))
    return f"<span style='background-color: {color}; color: white; padding: 5px 10px; border-radius: 3px;'>{status}</span>"


def calculate_trend(current: float, previous: float) -> Tuple[float, str]:
    """
    Calculate trend and direction

    Returns:
        (percent_change, direction)
    """
    if previous == 0:
        return 0, "➡️"

    percent_change = ((current - previous) / previous) * 100

    if percent_change > 5:
        return percent_change, "📈"
    elif percent_change < -5:
        return percent_change, "📉"
    else:
        return percent_change, "➡️"


def convert_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    """Convert API response list to DataFrame"""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def resample_timeseries(df: pd.DataFrame, date_column: str, freq: str = 'D') -> pd.DataFrame:
    """Resample time series data"""
    if df.empty or date_column not in df.columns:
        return df

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.set_index(date_column).resample(freq).mean().reset_index()
    return df


def get_forecast_colors(model_name: str) -> str:
    """Get color for forecast model"""
    colors = {
        "baseline": "#808080",
        "arima": "#1f77b4",
        "prophet": "#ff7f0e",
        "xgboost": "#2ca02c",
        "lightgbm": "#d62728",
        "ensemble": "#9467bd"
    }
    return colors.get(model_name, COLORS["primary"])


def format_confidence_interval(lower: float, upper: float) -> str:
    """Format confidence interval"""
    return f"[{lower:.0f}, {upper:.0f}]"


def get_days_ago(date_str: str) -> int:
    """Calculate days ago from date string"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        days = (datetime.now() - date_obj).days
        return max(0, days)
    except:
        return 0


def calculate_data_quality_score(freshness_data: Dict) -> float:
    """Calculate overall data quality score"""
    if not freshness_data or "sources" not in freshness_data:
        return 0.0

    sources = freshness_data["sources"]
    if not sources:
        return 0.0

    status_weights = {"fresh": 1.0, "stale": 0.5, "missing": 0.0}

    total_score = sum(
        status_weights.get(s.get("status", "missing"), 0) for s in sources
    )

    return (total_score / len(sources)) * 100


def format_uptime(seconds: int) -> str:
    """Format uptime from seconds"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    elif seconds < 86400:
        return f"{seconds // 3600}h"
    else:
        return f"{seconds // 86400}d"


def create_empty_dataframe_placeholder() -> pd.DataFrame:
    """Create placeholder DataFrame for empty data"""
    return pd.DataFrame({
        "Date": [],
        "Value": [],
        "Status": []
    })


def calculate_admission_change(current: float, previous: float) -> Tuple[float, str]:
    """
    Calculate admission value change from previous period

    Returns:
        (change_percent, direction_emoji)
    """
    if previous == 0:
        return 0, "➡️"

    percent_change = ((current - previous) / previous) * 100

    if percent_change > 10:
        return percent_change, "📈"
    elif percent_change < -10:
        return percent_change, "📉"
    else:
        return percent_change, "➡️"


def format_admission_value(value: float) -> str:
    """Format admission count with thousands separator"""
    if value is None or np.isnan(value):
        return "N/A"
    return f"{int(value):,}"


def get_data_sources(api_client: APIClient) -> Optional[Dict]:
    """Get list of configured data sources"""
    return api_client.get("/api/v1/data/sources")


def get_data_locations(api_client: APIClient) -> Optional[Dict]:
    """Get list of available locations with data"""
    return api_client.get("/api/v1/data/locations")


def get_data_summary(api_client: APIClient) -> Optional[Dict]:
    """Get overall pipeline status summary"""
    return api_client.get("/api/v1/data/summary")


def get_forecast_comparison(
    api_client: APIClient, location: str, horizon: int, days: int = 90
) -> Optional[Dict]:
    """Get forecast comparison data for location and horizon over time"""
    return api_client.get(f"/api/v1/forecasts/compare/{location}/{horizon}", params={"days": days})


def get_forecast_by_location(
    api_client: APIClient, location: str, days: int = 365
) -> Optional[Dict]:
    """Get forecast history for a specific location"""
    return api_client.get(f"/api/v1/forecasts/by-location/{location}", params={"days": days})


def get_available_models(api_client: APIClient) -> Optional[Dict]:
    """Get list of available forecast models"""
    return api_client.get("/api/v1/forecasts/models")


def get_available_locations(api_client: APIClient) -> Optional[Dict]:
    """Get list of available forecast locations"""
    return api_client.get("/api/v1/forecasts/locations")


def get_surveillance_current(
    api_client: APIClient, location: Optional[str] = None, limit: int = 10
) -> Optional[Dict]:
    """Get current admission data"""
    params = {"limit": limit}
    if location:
        params["location"] = location
    return api_client.get("/api/v1/surveillance/current", params=params)


def get_surveillance_by_location(
    api_client: APIClient, location: str, days: int = 90
) -> Optional[Dict]:
    """Get admission data for a specific location"""
    return api_client.get(f"/api/v1/surveillance/by-location/{location}", params={"days": days})


def get_surveillance_historical(
    api_client: APIClient, location: Optional[str] = None, days: int = 365
) -> Optional[Dict]:
    """Get historical admission data"""
    params = {"days": days}
    if location:
        params["location"] = location
    return api_client.get("/api/v1/surveillance/historical", params=params)


def get_surveillance_merged(
    api_client: APIClient, location: Optional[str] = None, limit: int = 100
) -> Optional[Dict]:
    """Get merged admission data (current + historical)"""
    params = {"limit": limit, "data_type": "merged"}
    if location:
        params["location"] = location
    return api_client.get("/api/v1/surveillance", params=params)


def get_surveillance_locations(api_client: APIClient) -> Optional[Dict]:
    """Get list of available admission locations"""
    return api_client.get("/api/v1/surveillance/locations")


def get_surveillance_summary(api_client: APIClient, location: str) -> Optional[Dict]:
    """Get admission summary for a specific location"""
    return api_client.get(f"/api/v1/surveillance/summary/{location}")


# Surveillance Data Endpoints (New)

def get_surveillance_historical(
    api_client: APIClient, location: str = None, days: int = None
) -> Optional[Dict]:
    """Get historical surveillance data (5+ years)"""
    params = {}
    if location:
        params["location"] = location
    if days:
        params["days"] = days
    return api_client.get("/api/v1/surveillance/historical", params=params)


def get_surveillance_current(
    api_client: APIClient, location: str = None, limit: int = 100
) -> Optional[Dict]:
    """Get current surveillance data (recent ~4 weeks, updated daily)"""
    params = {"limit": limit}
    if location:
        params["location"] = location
    return api_client.get("/api/v1/surveillance/current", params=params)


def get_surveillance_forecast(
    api_client: APIClient, location: str = None, limit: int = 100
) -> Optional[Dict]:
    """Get forecast surveillance data (up to 8 weeks ahead)"""
    params = {"limit": limit}
    if location:
        params["location"] = location
    return api_client.get("/api/v1/surveillance/forecasts", params=params)


def get_surveillance_merged(
    api_client: APIClient, location: str = None, limit: int = 100
) -> Optional[Dict]:
    """Get merged surveillance data (historical + current + forecast up to 8 weeks ahead)"""
    params = {"limit": limit}
    if location:
        params["location"] = location
    return api_client.get("/api/v1/surveillance/merged", params=params)


def get_surveillance_locations(api_client: APIClient) -> Optional[Dict]:
    """Get available locations with surveillance data"""
    return api_client.get("/api/v1/surveillance/locations")


def get_health_live(api_client: APIClient) -> Optional[Dict]:
    """Get health liveness check"""
    return api_client.get("/api/v1/health/live")


def get_health_ready(api_client: APIClient) -> Optional[Dict]:
    """Get health readiness check"""
    return api_client.get("/api/v1/health/ready")


def get_forecasts_by_date(
    api_client: APIClient, forecast_date: str
) -> Optional[Dict]:
    """Get forecasts issued on a specific date"""
    return api_client.get(f"/api/v1/forecasts/by-date/{forecast_date}")


def convert_epiweek_to_date(epiweek: int) -> str:
    """
    Convert CDC epiweek (YYYYWW) to ISO date string (YYYY-MM-DD)

    The CDC epiweek system defines week 1 as the first week with at least 4 days
    in January. This function returns the Sunday of that epiweek.

    Args:
        epiweek: Epidemiological week in YYYYWW format (e.g., 202603 = 2026 week 3)

    Returns:
        ISO date string representing the Sunday of that epiweek

    Example:
        >>> convert_epiweek_to_date(202603)
        '2026-01-19'
    """
    if epiweek is None or epiweek <= 0:
        return "N/A"

    try:
        year = epiweek // 100
        week = epiweek % 100

        if week < 1 or week > 53:
            return "N/A"

        # CDC epiweek starts on Sunday
        # Week 1 is the first week with at least 4 days in January
        # Find January 4th (always in week 1 by definition)
        jan_4th = datetime(year, 1, 4)

        # Find the Sunday of week 1
        # weekday() returns 0-6 (Mon-Sun), so Sunday is 6
        days_to_sunday = (6 - jan_4th.weekday()) % 7
        week_1_sunday = jan_4th + timedelta(days=days_to_sunday)

        # If we went forward past week 1, go back 1 week
        if days_to_sunday > 3:
            week_1_sunday -= timedelta(weeks=1)

        # Calculate target Sunday
        target_sunday = week_1_sunday + timedelta(weeks=week - 1)

        return target_sunday.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "N/A"
