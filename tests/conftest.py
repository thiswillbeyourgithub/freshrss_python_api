import os
import pytest
from freshrss_api import FreshRSSAPI

@pytest.fixture
def freshrss_client():
    """
    Fixture that provides a configured FreshRSS API client.

    Requires the following environment variables:
    - PYTEST_FRESHRSS_PYTHON_API_HOST
    - PYTEST_FRESHRSS_PYTHON_API_USERNAME
    - PYTEST_FRESHRSS_PYTHON_API_PASSWORD
    
    These will be mapped to the corresponding FRESHRSS_PYTHON_API_* environment variables.
    """
    host = os.environ.get('PYTEST_FRESHRSS_PYTHON_API_HOST')
    username = os.environ.get('PYTEST_FRESHRSS_PYTHON_API_USERNAME')
    password = os.environ.get('PYTEST_FRESHRSS_PYTHON_API_PASSWORD')

    if not all([host, username, password]):
        pytest.skip("Missing required environment variables for FreshRSS API tests")

    # Set the environment variables for FreshRSSAPI
    os.environ['FRESHRSS_PYTHON_API_HOST'] = host
    os.environ['FRESHRSS_PYTHON_API_USERNAME'] = username
    os.environ['FRESHRSS_PYTHON_API_PASSWORD'] = password
    os.environ['FRESHRSS_PYTHON_API_VERIFY_SSL'] = 'false'
    
    # Use the environment variables for authentication
    return FreshRSSAPI(verify_ssl=False)
