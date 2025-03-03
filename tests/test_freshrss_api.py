import pytest
from freshrss_api import FreshRSSAPI
import os


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
    test_host = host or os.environ.get("PYTEST_FRESHRSS_PYTHON_API_HOST")
    test_username = username or os.environ.get("PYTEST_FRESHRSS_PYTHON_API_USERNAME")
    test_password = password or os.environ.get("PYTEST_FRESHRSS_PYTHON_API_PASSWORD")

    if not all([test_host, test_username, test_password]):
        missing = []
        if not test_host:
            missing.append("host")
        if not test_username:
            missing.append("username")
        if not test_password:
            missing.append("password")
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    # Set the environment variables for FreshRSSAPI
    os.environ["FRESHRSS_PYTHON_API_HOST"] = test_host
    os.environ["FRESHRSS_PYTHON_API_USERNAME"] = test_username
    os.environ["FRESHRSS_PYTHON_API_PASSWORD"] = test_password
    os.environ["FRESHRSS_PYTHON_API_VERIFY_SSL"] = str(verify_ssl).lower()

    # Use the environment variables for authentication
    return FreshRSSAPI(verify_ssl=verify_ssl)


def test_freshrss_api(
    host: str = None,
    username: str = None,
    password: str = None,
    verify_ssl: bool = False,
):
    """
    Test the FreshRSS API client functionality.

    Args:
        host: FreshRSS host URL (defaults to PYTEST_FRESHRSS_PYTHON_API_HOST env var)
        username: FreshRSS username (defaults to PYTEST_FRESHRSS_PYTHON_API_USERNAME env var)
        password: FreshRSS password (defaults to PYTEST_FRESHRSS_PYTHON_API_PASSWORD env var)
        verify_ssl: Whether to verify SSL certificates

    Returns:
        True if all tests pass, raises AssertionError otherwise
    """
    inst = get_freshrss_client(host, username, password, verify_ssl)

    # Test feeds endpoint
    feeds = inst.get_feeds()
    assert feeds is not None, "Failed to retrieve feeds"
    assert isinstance(feeds, dict), "Feeds should be returned as a dictionary"
    feed_count = len(feeds)
    assert feed_count >= 0, "Feed count should be a non-negative number"
    print(f"✓ Successfully retrieved {feed_count} feeds")

    # Test items endpoint
    items = inst.get_items()
    assert items is not None, "Failed to retrieve items"
    assert isinstance(items, list), "Items should be returned as a list"
    item_count = len(items)
    assert item_count >= 0, "Item count should be a non-negative number"
    print(f"✓ Successfully retrieved {item_count} items")

    # Test item structure if items exist
    if items:
        item = items[0]
        assert hasattr(item, "id"), "Item should have an id attribute"
        assert hasattr(item, "title"), "Item should have a title attribute"
        assert hasattr(item, "url"), "Item should have a url attribute"
        assert hasattr(item, "readable"), "Item should have a readable attribute"
        print(f"✓ Item structure validation passed")

    # Test get_all_items with limit
    print(f"Fetching up to 100 items...")
    all_items = inst.get_all_items(n_max=100, verbose=True)
    assert all_items is not None, "Failed to retrieve all items"
    assert isinstance(all_items, list), "All items should be returned as a list"
    assert len(all_items) <= 100, "Should not exceed the requested limit of 100 items"
    print(f"✓ Successfully retrieved {len(all_items)} items with pagination")

    print("\n✓ All tests passed successfully!")
    return True


if __name__ == "__main__":
    try:
        fire.Fire(test_freshrss_api)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        exit(1)


def test_get_feeds(freshrss_client):
    """Test that we can retrieve feeds from the API."""
    feeds = freshrss_client.get_feeds()
    assert feeds is not None
    assert isinstance(feeds, dict)


def test_get_items(freshrss_client):
    """Test that we can retrieve items from the API."""
    items = freshrss_client.get_items()
    assert items is not None
    assert isinstance(items, list)

    # If there are items, check their structure
    if items:
        item = items[0]
        assert hasattr(item, "id")
        assert hasattr(item, "title")
        assert hasattr(item, "url")
        assert hasattr(item, "readable")


def test_get_all_items(freshrss_client):
    """Test that we can retrieve all items with pagination."""
    all_items = freshrss_client.get_all_items(n_max=100)
    assert all_items is not None
    assert isinstance(all_items, list)
    assert len(all_items) <= 100
