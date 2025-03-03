import pytest
from freshrss_api import FreshRSSAPI

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
        assert hasattr(item, 'id')
        assert hasattr(item, 'title')
        assert hasattr(item, 'url')
        assert hasattr(item, 'readable')

def test_get_all_items(freshrss_client):
    """Test that we can retrieve all items with pagination."""
    # Limit to 10 items for test speed
    all_items = freshrss_client.get_all_items(n_max=10)
    assert all_items is not None
    assert isinstance(all_items, list)
    assert len(all_items) <= 10
