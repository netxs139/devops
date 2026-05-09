import os
from typing import Any

import requests
import streamlit as st


class ApiClient:
    """
    Standard API client for Streamlit dashboard to communicate with FastAPI backend.
    Ensures consistent timeout, error handling, and URL management.
    """

    def __init__(self, base_url: str = os.getenv("API_URL", "http://api:8000")):
        self.base_url = base_url.rstrip("/")

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Perform a GET request to the backend."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Backend API Error [{endpoint}]: {e}")
            return None

    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Perform a POST request to the backend."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Backend API Error [{endpoint}]: {e}")
            return None


# Singleton instance
api_client = ApiClient()
