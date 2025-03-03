from datetime import datetime
import hashlib
import os
import random
import requests
import time

MINIMUM_VALID_TIMESTAMP = 946684800  # January 1, 2000 00:00:00 UTC
from typing import Union, Optional, Dict, Any, Literal
from urllib.parse import urljoin

try:
    from beartype import beartype as optional_typecheck
except ImportError:

    def optional_typecheck(callable):
        return callable


from .utils.items import Item
from .utils.errors import APIError, AuthenticationError


@optional_typecheck
class FreshRSSAPI:
    """A Python client for the FreshRSS Fever API."""

    VERSION: str = "1.0.1"

    def __init__(
        self,
        host: str = None,
        username: str = None,
        password: str = None,
        verify_ssl: bool = True,
    ):
        """
        Initialize the FreshRSS API client.

        API sources:
        - https://freshrss.github.io/FreshRSS/en/developers/06_Fever_API.html
        - https://web.archive.org/web/20230616124016/https://feedafever.com/api
        - https://github.com/Alkarex/FreshRSS/blob/989d8f2cb71766a4d2803c3853a4007b0a3556bf/docs/fr/users/06_Mobile_access.md

        Args:
            host: Base URL of FreshRSS instance (e.g., 'https://freshrss.example.net')
                 Defaults to FRESHRSS_PYTHON_API_HOST environment variable if not provided
            username: FreshRSS username
                     Defaults to FRESHRSS_PYTHON_API_USERNAME environment variable if not provided
            password: FreshRSS API password
                     Defaults to FRESHRSS_PYTHON_API_PASSWORD environment variable if not provided
            verify_ssl: Whether to verify SSL certificates (default: True)
                       Can be overridden with FRESHRSS_PYTHON_API_VERIFY_SSL environment variable
        """
        # Get values from environment variables if not provided
        self.host = host or os.environ.get("FRESHRSS_PYTHON_API_HOST")
        username = username or os.environ.get("FRESHRSS_PYTHON_API_USERNAME")
        password = password or os.environ.get("FRESHRSS_PYTHON_API_PASSWORD")

        # Check for required values
        if not self.host:
            raise ValueError(
                "Host URL is required. Provide it as an argument or set FRESHRSS_PYTHON_API_HOST environment variable."
            )
        if not username:
            raise ValueError(
                "Username is required. Provide it as an argument or set FRESHRSS_PYTHON_API_USERNAME environment variable."
            )
        if not password:
            raise ValueError(
                "Password is required. Provide it as an argument or set FRESHRSS_PYTHON_API_PASSWORD environment variable."
            )

        # Check if verify_ssl is set in environment
        env_verify_ssl = os.environ.get("FRESHRSS_PYTHON_API_VERIFY_SSL")
        if env_verify_ssl is not None:
            verify_ssl = env_verify_ssl.lower() in ("true", "1", "yes")
        self.host = self.host.rstrip("/")
        self.api_endpoint = urljoin(f"{self.host}/api/", "fever.php")
        self.verify_ssl = verify_ssl

        # Calculate API key (MD5 hash of "username:password")
        self.api_key = hashlib.md5(f"{username}:{password}".encode()).hexdigest()

        # Verify authentication on initialization
        self._check_auth()

    def _check_auth(self) -> None:
        """Verify API authentication works."""
        response = self._call("api")
        if not response.get("auth"):
            raise AuthenticationError("Failed to authenticate with FreshRSS API")

    def _call(self, endpoint: str, **params: Any) -> Dict[str, Any]:
        """
        Make a call to the FreshRSS Fever API.

        Args:
            endpoint: API endpoint to call
            **params: Additional parameters to include in the request

        Returns:
            Dict containing the API response

        Raises:
            APIError: If the API request fails
            AuthenticationError: If authentication fails
        """
        # Prepare request parameters
        data = {"api_key": self.api_key}

        # Build query parameters
        query_params = {"api": ""}
        if endpoint != "api":
            query_params[endpoint] = ""
        query_params.update(params)

        try:
            response = requests.post(
                self.api_endpoint,
                params=query_params,
                data=data,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()

            # Check authentication
            if not result.get("auth"):
                raise AuthenticationError("Invalid API credentials")

            return result

        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise APIError(f"Failed to parse API response: {str(e)}")

    def set_mark(
        self, as_: Literal["read", "unread"], id: Union[str, int]
    ) -> Dict[str, Any]:
        """
        Mark an item as read or unread.

        Args:
            as_: Status to set ('read' or 'unread')
            id: ID of the item to mark

        Returns:
            Dict containing the API response
        """
        return self._call("mark", as_=as_, id=str(id))

    def _dict_to_item(self, item_dict: Dict[str, Any]) -> Item:
        """Convert a dictionary to an Item object."""
        return Item(
            id=int(item_dict["id"]),
            feed_id=int(item_dict["feed_id"]),
            title=item_dict["title"],
            author=item_dict["author"],
            html=item_dict["html"],
            url=item_dict["url"],
            is_saved=bool(item_dict["is_saved"]),
            is_read=bool(item_dict["is_read"]),
            created_on_time=int(item_dict["created_on_time"]),
        )

    def get_items(
        self,
        since_id: Union[str, int, None] = None,
        max_id: Union[str, int, None] = None,
        with_id: Optional[list[int]] = None,
    ) -> list[Item]:
        """
        Get items from the FreshRSS instance.

        Args:
            since_id: Optional ID to get items newer than this ID
            max_id: Optional ID to get items older than this ID
            with_id: Optional list of item IDs to retrieve

        Returns:
            List of Item objects
        """
        params = {}
        if since_id is not None:
            params["since_id"] = str(since_id)
        if max_id is not None:
            params["max_id"] = str(max_id)
        if with_id is not None:
            params["with_ids"] = ",".join(str(id) for id in with_id)

        response = self._call("items", **params)
        return [self._dict_to_item(item) for item in response.get("items", [])]

    def get_all_items(
        self, timeout: int = 300, verbose: bool = False, n_max: Optional[int] = None
    ) -> list[Item]:
        """
        Get all items from the FreshRSS instance by making multiple requests.

        Args:
            timeout: Maximum time in seconds to spend fetching all items (default: 300)
            verbose: If True, prints progress information during fetching (default: False)
            n_max: Optional maximum number of items to retrieve. It only accepts multiple of 50 because of the way Fever works (default: None)

        Returns:
            List of Item objects
        """
        assert n_max % 50 == 0, "n_max argument can only be a multiple of 50"
        all_items = []
        current_since_id = 0  # Start with 0 to get newest items
        start_time = time.time()
        earliest_time = None
        latest_time = None

        while True:
            if time.time() - start_time > timeout:
                if verbose:
                    print(f"Reached timeout limit of {timeout} seconds")
                break

            # Random sleep between requests to avoid rate limits
            time.sleep(random.uniform(0.5, 1.5))

            items = self.get_items(since_id=str(current_since_id))
            if not items:
                break

            all_items.extend(items)

            # Check if we've reached n_max items
            if n_max is not None and len(all_items) >= n_max:
                if verbose:
                    print(f"Reached maximum requested items ({n_max})")
                break

            # Update timestamp tracking
            batch_times = [item.created_on_time for item in items]
            min_batch_time = min(batch_times)
            max_batch_time = max(batch_times)

            # Only update earliest_time if the date is valid (after year 2000)
            if min_batch_time >= MINIMUM_VALID_TIMESTAMP:
                if earliest_time is None or min_batch_time < earliest_time:
                    earliest_time = min_batch_time

            if latest_time is None or max_batch_time > latest_time:
                latest_time = max_batch_time

            if verbose:
                print(
                    f"Found {len(items)} new items. Total items so far: {len(all_items)}"
                )
                if n_max:
                    percentage = (len(all_items) / n_max) * 100
                    print(f"Progress: {percentage:.1f}%")

                # Print time range if we have valid timestamps
                if earliest_time is not None and latest_time is not None:
                    earliest_dt = datetime.fromtimestamp(earliest_time)
                    latest_dt = datetime.fromtimestamp(latest_time)
                    print(f"Time range: {earliest_dt} to {latest_dt}")
                    print(f"Earliest item: {earliest_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Latest item: {latest_dt.strftime('%Y-%m-%d %H:%M:%S')}")

            # Update since_id for next iteration - use the lowest ID from current batch
            current_since_id = min(item.id for item in items)

            if current_since_id <= 0:
                break

        if verbose:
            elapsed = time.time() - start_time
            print(
                f"\nCompleted fetching {len(all_items)} items in {elapsed:.2f} seconds"
            )
            if earliest_time is not None and latest_time is not None:
                time_span = latest_time - earliest_time
                print(f"Total time span of items: {time_span/86400:.1f} days")

        return all_items

    def get_feeds(self) -> Dict[str, Any]:
        """
        Get all feeds from the FreshRSS instance.

        Returns:
            Dict containing feeds data
        """
        return self._call("feeds")

    def get_groups(self) -> Dict[str, Any]:
        """
        Get all groups (categories) from the FreshRSS instance.

        Returns:
            Dict containing groups data
        """
        return self._call("groups")

    def get_unreads(self) -> list[Item]:
        """
        Get all unread items from the FreshRSS instance.

        Returns:
            List of unread Item objects
        """
        unread_ids = self._call("unread_item_ids").get("unread_item_ids", "").split(",")
        if unread_ids and unread_ids[0]:  # Check if we have any IDs
            items = self.get_items(with_id=[int(id) for id in unread_ids])
            return items
        return []

    def get_saved(self) -> list[Item]:
        """
        Get all saved (starred) items from the FreshRSS instance.

        Returns:
            List of saved Item objects
        """
        saved_ids = self._call("saved_item_ids").get("saved_item_ids", "").split(",")
        if saved_ids and saved_ids[0]:  # Check if we have any IDs
            items = self.get_items(with_id=[int(id) for id in saved_ids])
            return items
        return []
