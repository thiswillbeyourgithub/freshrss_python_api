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
     """
     host = os.environ.get('PYTEST_FRESHRSS_PYTHON_API_HOST')
     username = os.environ.get('PYTEST_FRESHRSS_PYTHON_API_USERNAME')
     password = os.environ.get('PYTEST_FRESHRSS_PYTHON_API_PASSWORD')

     if not all([host, username, password]):
         pytest.skip("Missing required environment variables for FreshRSS API tests")

     return FreshRSSAPI(
         host=host,
         username=username,
         password=password,
         verify_ssl=False,
     )
