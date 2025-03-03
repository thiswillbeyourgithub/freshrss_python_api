class APIError(Exception):
    """Raised when an API request fails."""

    pass


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    pass
