from datetime import datetime, timezone
import hashlib
import os
import random
import requests
import time

MINIMUM_VALID_TIMESTAMP = 946684800  # January 1, 2000 00:00:00 UTC
from typing import Union, Optional, Dict, Any, Literal
from urllib.parse import urljoin
from loguru import logger

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

    VERSION: str = "2.0.0"

    def __init__(
        self,
        host: str = None,
        username: str = None,
        password: str = None,
        verify_ssl: bool = True,
        verbose: bool = False,
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
        self.verbose = verbose

        # Calculate API key (MD5 hash of "username:password")
        self.api_key = hashlib.md5(f"{username}:{password}".encode()).hexdigest()

        # Verify authentication on initialization
        self._check_auth()

    def _check_auth(self) -> None:
        """Verify API authentication works."""
        response = self._call("api")
        if not response.get("auth"):
            raise AuthenticationError("Failed to authenticate with FreshRSS API")

    def _call(self, endpoint: str = "api", **params: Any) -> Dict[str, Any]:
        """
        Make a call to the FreshRSS Fever API.

        Args:
            endpoint: API endpoint to call. Defaults to 'api'.
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
        if "as_" in query_params:  # as is a python keyword
            query_params["as"] = query_params["as_"]
            del query_params["as_"]

        if self.verbose:
            logger.info(f"API request: {self.api_endpoint}")
            logger.info(f"Query parameters: {query_params}")

        retry_count = 0
        max_retries = 1
        retry_delay = 2  # seconds

        while True:
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

                if self.verbose:
                    logger.info(f"API response: {result}")

                return result

            except (requests.exceptions.RequestException, ValueError) as e:
                retry_count += 1
                error_type = (
                    "API request"
                    if isinstance(e, requests.exceptions.RequestException)
                    else "JSON parsing"
                )

                if retry_count <= max_retries:
                    if self.verbose:
                        logger.warning(
                            f"{error_type} failed, retrying in {retry_delay}s: {str(e)}"
                        )
                    time.sleep(retry_delay)
                else:
                    if isinstance(e, requests.exceptions.RequestException):
                        raise APIError(f"API request failed after retry: {str(e)}")
                    else:
                        raise APIError(
                            f"Failed to parse API response after retry: {str(e)}"
                        )

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

    @staticmethod
    def _date_to_id(date_str: str, date_format: str = "%Y-%m-%d") -> int:
        """
        Convert a date string to a millisecond timestamp integer.

        This can be useful for converting dates to IDs for API queries.

        Args:
            date_str: Date string to convert (e.g., '2023-01-15')
            date_format: Format string for parsing the date (e.g., '%Y-%m-%d', default: '%Y-%m-%d')

        Returns:
            Integer timestamp in milliseconds

        Example:
            >>> FreshRSSAPI._date_to_id('2023-01-15')
            1673740800000000000
        """
        dt = datetime.strptime(date_str, date_format)
        # Ensure the datetime is timezone-aware (UTC)
        dt = dt.replace(tzinfo=timezone.utc)
        # Convert to milliseconds (seconds * 10^6)
        return int(dt.timestamp() * 1_000_000)

    def set_mark(
        self, as_: Literal["read", "saved", "unsaved"], id: Union[str, int]
    ) -> Dict[str, Any]:
        """
        Mark an item as read or saved/unsaved. Fever_API can handle
        setting marks to other things than items but this is not implemented
        here. Marking as 'unread' is not possible either.

        Args:
            as_: Status to set ('read', 'saved', or 'unsaved')
            id: ID of the item to mark

        Returns:
            Dict containing the API response
        """
        assert as_ != "unread", "The Fever_API does not support marking as 'unread'"
        resp = self._call(mark="item", as_=as_, id=id)

        if as_ == "read":
            if not "read_item_ids" in resp:
                logger.error(
                    f"The response to set_mark does not contain 'read_item_ids'"
                )
        elif as_ == "saved":
            if not "saved_item_ids" in resp:
                logger.error(
                    f"The response to set_mark does not contain 'saved_item_ids'"
                )
        elif as_ == "unsaved":
            if not "saved_item_ids" in resp:
                logger.error(
                    f"The response to set_mark does not contain 'saved_item_ids'"
                )

        return resp

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
        if not (unread_ids and unread_ids[0]):  # Check if we have any IDs
            return []
        items = self.get_items_from_ids(ids=[int(id) for id in unread_ids])
        return items

    def get_saved(self) -> list[Item]:
        """
        Get all saved (starred) items from the FreshRSS instance.

        Returns:
            List of saved Item objects
        """
        saved_ids = self._call("saved_item_ids").get("saved_item_ids", "").split(",")
        if not (saved_ids and saved_ids[0]):  # Check if we have any IDs
            return []
        items = self.get_items_from_ids(ids=[int(id) for id in saved_ids])
        return items

    def get_items_from_ids(self, ids: list[int]) -> list[Item]:
        """
        Get items by their IDs from the FreshRSS instance.

        This method handles batching of requests (max 50 IDs per request)
        and verifies that all requested items are returned.

        Args:
            ids: List of item IDs to retrieve

        Returns:
            List of Item objects corresponding to the requested IDs

        Raises:
            APIError: If the API doesn't return all requested items
        """
        if not ids:
            return []

        all_items = []
        total_requested = len(ids)

        # Process in batches of 50
        for i in range(0, total_requested, 50):
            batch = ids[i : i + 50]
            batch_params = {"with_ids": ",".join(str(id) for id in batch)}

            response = self._call("items", **batch_params)
            all_items.extend(
                [self._dict_to_item(item) for item in response.get("items", [])]
            )

        # Verify we got all the items we requested
        if len(all_items) != total_requested:
            raise APIError(
                f"API returned {len(all_items)} items but {total_requested} were requested. "
                f"Some items may not exist or may not be accessible."
            )

        # Sort items by ID
        all_items.sort(key=lambda item: item.id)

        return all_items

    def get_items_from_dates(
        self,
        since: Union[str, int, datetime, None] = None,
        until: Union[str, int, datetime, None] = None,
        date_format: str = "%Y-%m-%d",
    ) -> list[Item]:
        """
        Get items between two dates or timestamps.

        Args:
            since: Starting date/time (inclusive). Can be:
                   - A string in the format specified by date_format
                   - A datetime object
                   - An integer timestamp
                   - None (will raise an error as this is required)
            until: Ending date/time (inclusive). Can be:
                   - A string in the format specified by date_format
                   - A datetime object
                   - An integer timestamp
                   - None (defaults to current time)
            date_format: Format string for parsing date strings (default: '%Y-%m-%d')

        Returns:
            List of Item objects between the specified dates

        Raises:
            ValueError: If since is None or if since is greater than or equal to until

        Example:
            >>> api.get_items_from_dates('2023-01-01', '2023-01-31')
            [Item(...), Item(...), ...]
        """
        # Ensure since is provided
        if since is None:
            raise ValueError("The 'since' parameter is required")

        # Convert since to timestamp if it's not already
        if isinstance(since, str):
            since_id = self._date_to_id(since, date_format)
        elif isinstance(since, datetime):
            since_id = int(since.timestamp() * 1_000_000)
        else:
            since_id = int(since)

        # Convert until to timestamp if provided, otherwise use current time
        if until is None:
            until_id = int(datetime.now(timezone.utc).timestamp() * 1_000_000)
        elif isinstance(until, str):
            until_id = self._date_to_id(until, date_format)
        elif isinstance(until, datetime):
            until_id = int(until.timestamp() * 1_000_000)
        else:
            until_id = int(until)

        # Validate that since is before until
        assert (
            since_id < until_id
        ), "The 'since' date must be earlier than the 'until' date"

        all_items = []
        seen_ids = set()
        current_since_id = since_id

        while True:
            # Fetch a batch of items
            response = self._call("items", since_id=str(current_since_id))
            items_batch = response.get("items", [])

            # If no items returned, we're done
            if not items_batch:
                break

            # Process items, filtering by until_id
            new_items = []
            highest_id = current_since_id

            for item_dict in items_batch:
                item_id = int(item_dict["id"])

                # Skip if we've already seen this ID
                if item_id in seen_ids:
                    continue

                # Skip if item is beyond our until date
                if item_id > until_id:
                    continue

                # Add to our results
                new_items.append(self._dict_to_item(item_dict))
                seen_ids.add(item_id)

                # Track highest ID for next iteration
                highest_id = max(highest_id, item_id)

            # Add filtered items to our results
            all_items.extend(new_items)

            # If we got fewer than 50 items, we've reached the end
            if len(items_batch) < 50:
                break

            # Update since_id for next iteration
            current_since_id = highest_id

            # Verify no duplicates - crash if we find any
            if len(all_items) != len(seen_ids):
                raise RuntimeError(
                    f"Duplicate item IDs detected in results! This should never happen. "
                    f"Items count: {len(all_items)}, Unique IDs count: {len(seen_ids)}"
                )

        # Sort items by ID before returning
        all_items.sort(key=lambda item: item.id)

        return all_items
