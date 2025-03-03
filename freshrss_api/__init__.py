from .freshrss_api import FreshRSSAPI, Item, APIError, AuthenticationError

__VERSION__ = FreshRSSAPI.VERSION

__all__ = ["FreshRSSAPI", "Item", "APIError", "AuthenticationError"]
