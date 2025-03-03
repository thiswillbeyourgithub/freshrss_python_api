import os
from freshrss_api import FreshRSSAPI
import fire

def get_freshrss_client(
    host: str = None,
    username: str = None,
    password: str = None,
    verify_ssl: bool = False,
):
    """
    Create a FreshRSS API client using provided credentials or environment variables.
    
    Args:
        host: FreshRSS host URL (defaults to PYTEST_FRESHRSS_PYTHON_API_HOST env var)
        username: FreshRSS username (defaults to PYTEST_FRESHRSS_PYTHON_API_USERNAME env var)
        password: FreshRSS password (defaults to PYTEST_FRESHRSS_PYTHON_API_PASSWORD env var)
        verify_ssl: Whether to verify SSL certificates
        
    Returns:
        FreshRSSAPI instance
    """
    # Use provided values or fall back to environment variables
    test_host = host or os.environ.get('PYTEST_FRESHRSS_PYTHON_API_HOST')
    test_username = username or os.environ.get('PYTEST_FRESHRSS_PYTHON_API_USERNAME')
    test_password = password or os.environ.get('PYTEST_FRESHRSS_PYTHON_API_PASSWORD')
    
    if not all([test_host, test_username, test_password]):
        missing = []
        if not test_host: missing.append("host")
        if not test_username: missing.append("username")
        if not test_password: missing.append("password")
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")
    
    # Set the environment variables for FreshRSSAPI
    os.environ['FRESHRSS_PYTHON_API_HOST'] = test_host
    os.environ['FRESHRSS_PYTHON_API_USERNAME'] = test_username
    os.environ['FRESHRSS_PYTHON_API_PASSWORD'] = test_password
    os.environ['FRESHRSS_PYTHON_API_VERIFY_SSL'] = str(verify_ssl).lower()
    
    # Use the environment variables for authentication
    return FreshRSSAPI(verify_ssl=verify_ssl)

def freshrss_client(
    host: str = None,
    username: str = None,
    password: str = None,
    verify_ssl: bool = False,
):
    """
    FreshRSS API client demo.
    
    Args:
        host: FreshRSS host URL (defaults to PYTEST_FRESHRSS_PYTHON_API_HOST env var)
        username: FreshRSS username (defaults to PYTEST_FRESHRSS_PYTHON_API_USERNAME env var)
        password: FreshRSS password (defaults to PYTEST_FRESHRSS_PYTHON_API_PASSWORD env var)
        verify_ssl: Whether to verify SSL certificates
    """
    inst = get_freshrss_client(host, username, password, verify_ssl)

    print(f"{len(inst.get_feeds())} feeds")

    items = inst.get_items()
    print(f"{len(items)} items")
    if items:
        print(items[0].readable)
    
    print(f"Fetching 100 items...")
    all_items = inst.get_all_items(n_max=100, verbose=True)
    
    return all_items

if __name__ == "__main__":
    fire.Fire(freshrss_client)
