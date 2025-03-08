import pytest
from freshrss_api import FreshRSSAPI
import os
from datetime import datetime, timedelta


def get_freshrss_client(
    host: str = None,
    username: str = None,
    password: str = None,
    verify_ssl: bool = False,
    verbose: bool = False,
):
    """
    Create a FreshRSS API client using provided credentials or environment variables.

    Args:
        host: FreshRSS host URL (defaults to PYTEST_FRESHRSS_PYTHON_API_HOST env var)
        username: FreshRSS username (defaults to PYTEST_FRESHRSS_PYTHON_API_USERNAME env var)
        password: FreshRSS password (defaults to PYTEST_FRESHRSS_PYTHON_API_PASSWORD env var)
        verify_ssl: Whether to verify SSL certificates
        verbose: True to enable verbose logging.

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
    return FreshRSSAPI(verify_ssl=verify_ssl, verbose=verbose)


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
    feed_count = len(feeds.get("feeds", []))
    assert feed_count >= 0, "Feed count should be a non-negative number"
    print(f"✓ Successfully retrieved {feed_count} feeds")

    # Test groups endpoint
    groups = inst.get_groups()
    assert groups is not None, "Failed to retrieve groups"
    assert isinstance(groups, dict), "Groups should be returned as a dictionary"
    print(f"✓ Successfully retrieved groups")

    # Test unread items
    unread_items = inst.get_unreads()
    assert unread_items is not None, "Failed to retrieve unread items"
    assert isinstance(unread_items, list), "Unread items should be returned as a list"
    print(f"✓ Successfully retrieved {len(unread_items)} unread items")

    # Test saved items
    saved_items = inst.get_saved()
    assert saved_items is not None, "Failed to retrieve saved items"
    assert isinstance(saved_items, list), "Saved items should be returned as a list"
    print(f"✓ Successfully retrieved {len(saved_items)} saved items")

    # Test item structure if items exist
    if unread_items:
        item = unread_items[0]
        assert hasattr(item, "id"), "Item should have an id attribute"
        assert hasattr(item, "title"), "Item should have a title attribute"
        assert hasattr(item, "url"), "Item should have a url attribute"
        assert hasattr(item, "html"), "Item should have a html attribute"
        print(f"✓ Item structure validation passed")

    # Test get_items_from_dates
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(hours=3)

    print(
        f"Fetching items from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}..."
    )
    date_items = inst.get_items_from_dates(since=start_date, until=end_date)
    assert date_items is not None, "Failed to retrieve items by date"
    assert isinstance(date_items, list), "Items by date should be returned as a list"
    print(f"✓ Successfully retrieved {len(date_items)} items by date range")

    print("\n✓ All tests passed successfully!")
    return True


@pytest.fixture
def freshrss_client():
    """Fixture to provide a FreshRSS API client for tests."""
    # Skip tests if environment variables are not set
    required_vars = [
        "PYTEST_FRESHRSS_PYTHON_API_HOST",
        "PYTEST_FRESHRSS_PYTHON_API_USERNAME",
        "PYTEST_FRESHRSS_PYTHON_API_PASSWORD",
    ]

    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        pytest.skip(f"Missing required environment variables: {', '.join(missing)}")

    return get_freshrss_client()


def test_get_feeds(freshrss_client):
    """Test that we can retrieve feeds from the API."""
    feeds = freshrss_client.get_feeds()
    assert feeds is not None
    assert isinstance(feeds, dict)
    assert "feeds" in feeds


def test_get_groups(freshrss_client):
    """Test that we can retrieve groups from the API."""
    groups = freshrss_client.get_groups()
    assert groups is not None
    assert isinstance(groups, dict)
    assert "groups" in groups


def test_get_unreads(freshrss_client):
    """Test that we can retrieve unread items from the API."""
    items = freshrss_client.get_unreads()
    assert items is not None
    assert isinstance(items, list)

    # If there are items, check their structure
    if items:
        item = items[0]
        assert hasattr(item, "id")
        assert hasattr(item, "title")
        assert hasattr(item, "url")
        assert hasattr(item, "html")


def test_get_saved(freshrss_client):
    """Test that we can retrieve saved items from the API."""
    items = freshrss_client.get_saved()
    assert items is not None
    assert isinstance(items, list)


def test_date_to_id():
    """Test the _date_to_id static method."""
    # Test with a known date
    date_str = "2023-01-15"
    expected_id = 1673740800000000  # This is the timestamp for 2023-01-15 00:00:00 UTC in microseconds

    # Allow for small differences due to timezone handling
    result = FreshRSSAPI._date_to_id(date_str)
    assert abs(result - expected_id) < 86400000000  # Within one day in microseconds

    # Test with a different format
    date_str = "15/01/2023"
    result = FreshRSSAPI._date_to_id(date_str, date_format="%d/%m/%Y")
    assert abs(result - expected_id) < 86400000000  # Within one day in microseconds


def test_get_items_from_ids(freshrss_client):
    """Test that we can retrieve items by IDs."""
    # First get some unread items to get valid IDs
    unread_items = freshrss_client.get_unreads()

    if not unread_items:
        pytest.skip("No unread items available for testing get_items_from_ids")

    # Take up to 3 IDs for testing
    ids = [item.id for item in unread_items[:3]]

    # Test retrieving these specific items
    items = freshrss_client.get_items_from_ids(ids)
    assert items is not None
    assert isinstance(items, list)
    assert len(items) == len(ids)

    # Verify we got the correct items
    retrieved_ids = [item.id for item in items]
    assert sorted(retrieved_ids) == sorted(ids)


def test_get_items_from_dates(freshrss_client):
    """Test that we can retrieve items by date range."""
    # Test with last few moments
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=3)

    items = freshrss_client.get_items_from_dates(since=start_date, until=end_date)
    assert items is not None
    assert isinstance(items, list)

    # Test with string dates (including hours to distinguish times within the same day)
    items_str = freshrss_client.get_items_from_dates(
        since=start_date.strftime("%Y-%m-%d %H:%M:%S"),
        until=end_date.strftime("%Y-%m-%d %H:%M:%S"),
        date_format="%Y-%m-%d %H:%M:%S",
    )
    assert items_str is not None
    assert isinstance(items_str, list)


def test_set_mark(freshrss_client):
    """Test that we can mark items saved/unsaved. We don't test read as it's
    harder to reverse."""
    # First get some unread items to mark
    unread_items = freshrss_client.get_unreads()

    if not unread_items:
        pytest.skip("No unread items available for testing set_mark")

    # Take the first item for testing
    item = unread_items[0]

    # Not testing read because it cannot be undone.
    # Test marking as read
    # response = freshrss_client.set_mark(as_="read", id=item.id)
    # assert response is not None
    # assert isinstance(response, dict)
    # assert "read_item_ids" in response

    if item.is_saved:
        # Test marking as unsaved
        response = freshrss_client.set_mark(as_="unsaved", id=item.id)
        assert response is not None
        assert isinstance(response, dict)
        assert "saved_item_ids" in response

        # Test marking as saved
        response = freshrss_client.set_mark(as_="saved", id=item.id)
        assert response is not None
        assert isinstance(response, dict)
        assert "saved_item_ids" in response
    else:
        # Test marking as saved
        response = freshrss_client.set_mark(as_="saved", id=item.id)
        assert response is not None
        assert isinstance(response, dict)
        assert "saved_item_ids" in response

        # Test marking as unsaved
        response = freshrss_client.set_mark(as_="unsaved", id=item.id)
        assert response is not None
        assert isinstance(response, dict)
        assert "saved_item_ids" in response


if __name__ == "__main__":
    import fire

    try:
        fire.Fire(test_freshrss_api)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        exit(1)
