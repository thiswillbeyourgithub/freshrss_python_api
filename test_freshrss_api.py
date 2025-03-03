import pytest

def test_get_feeds(freshrss_client):
    """Test that we can retrieve feeds from the FreshRSS API."""
    feeds = freshrss_client.get_feeds()
    assert isinstance(feeds, dict)
    assert len(feeds) >= 0  # There might be no feeds, but it should be a valid response

def test_get_items(freshrss_client):
    """Test that we can retrieve items from the FreshRSS API."""
    items = freshrss_client.get_items()
    assert isinstance(items, list)
    
    # If there are items, check the first one has expected attributes
    if items:
        assert hasattr(items[0], 'id')
        assert hasattr(items[0], 'title')
        assert hasattr(items[0], 'url')

def test_get_all_items(freshrss_client):
    """Test that we can retrieve multiple items from the FreshRSS API."""
    items = freshrss_client.get_all_items(n_max=10)
    assert isinstance(items, list)
    assert len(items) <= 10  # Should respect the n_max parameter
