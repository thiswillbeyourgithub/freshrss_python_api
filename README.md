# FreshRSS Python API Client

[![PyPI Version](https://img.shields.io/pypi/v/freshrss-api)](https://pypi.org/project/freshrss-api/)
[![License](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)

A Python client for interacting with the FreshRSS Fever API. This library provides an easy-to-use interface for fetching items, marking items as read/saved/unsaved, and managing feeds and categories in your FreshRSS instance.

## Features

- **Authentication**: Securely authenticate with your FreshRSS instance using your username and API password or environment variables.
- **Item Management**: Fetch unread items, saved items, or items by ID or date range. Mark items as read, saved, or unsaved.
- **Feeds & Groups**: Retrieve all feeds and groups (categories) from your FreshRSS instance.
- **Date-based Queries**: Fetch items between specific dates with the `get_items_from_dates()` method.
- **Robust Error Handling**: Automatic retries for API requests with detailed error reporting.
- **Type Safety**: Optional type checking with `beartype` for improved code reliability.
- **Environment Variables**: Configure the client using environment variables for easier integration with CI/CD pipelines and containerized environments.
- **Verbose Logging**: Optional detailed logging of API requests and responses using Loguru.

## Installation

You can install the FreshRSS API client via pip:

```bash
pip install freshrss-api
```

## Usage

### Environment Variables

The FreshRSS API client supports the following environment variables:

- `FRESHRSS_PYTHON_API_HOST`: Your FreshRSS instance URL (e.g., "https://freshrss.example.net")
- `FRESHRSS_PYTHON_API_USERNAME`: Your FreshRSS username
- `FRESHRSS_PYTHON_API_PASSWORD`: Your FreshRSS API password
- `FRESHRSS_PYTHON_API_VERIFY_SSL`: Whether to verify SSL certificates ("true", "1", "yes" for True, anything else for False)

These environment variables can be used instead of passing parameters directly to the constructor.

### Initialization

To start using the FreshRSS API client, initialize it with your FreshRSS instance URL, username, and API password.

```python
from freshrss_api import FreshRSSAPI

# Initialize the client with direct parameters
client = FreshRSSAPI(
    host="https://freshrss.example.net",
    username="your_username",
    password="your_api_password",
    verify_ssl=True,
    verbose=False
)

# Or use environment variables
# export FRESHRSS_PYTHON_API_HOST="https://freshrss.example.net"
# export FRESHRSS_PYTHON_API_USERNAME="your_username"
# export FRESHRSS_PYTHON_API_PASSWORD="your_api_password"
# export FRESHRSS_PYTHON_API_VERIFY_SSL="true"
client = FreshRSSAPI()  # Will use environment variables
```

### Fetching Items

You can fetch unread items, saved items, or items by specific IDs or date ranges:

```python
# Fetch unread items
unread_items = client.get_unreads()

# Fetch saved items
saved_items = client.get_saved()

# Fetch items by IDs
items = client.get_items_from_ids([12345, 67890])

# Fetch items between dates
items = client.get_items_from_dates(
    since="2023-01-01",  # Can be string, datetime, or timestamp
    until="2023-01-31",  # Optional, defaults to current time
    date_format="%Y-%m-%d"  # Optional format string for date parsing
)
```

### Marking Items

Mark items as read, saved, or unsaved using the `set_mark` method:

```python
# Mark an item as read
client.set_mark(as_="read", id=12345)

# Mark an item as saved (starred)
client.set_mark(as_="saved", id=12345)

# Mark an item as unsaved (unstarred)
client.set_mark(as_="unsaved", id=12345)
```

Note: The Fever API does not support marking items as unread.

### Managing Feeds and Groups

Fetch all feeds or groups (categories) from your FreshRSS instance:

```python
# Get all feeds
feeds = client.get_feeds()

# Get all groups (categories)
groups = client.get_groups()
```

### Working with Dates and IDs

In the FreshRSS API, item IDs are timestamps in microseconds. The library provides a helper method to convert dates to IDs:

```python
# Convert a date string to an ID
id = FreshRSSAPI._date_to_id("2023-01-15")  # Static method

# Item objects have datetime properties
for item in items:
    print(f"Item created on: {item.created_datetime}")
    print(f"Item ID as datetime: {item.id_datetime}")
```

### Verbose Logging

Enable verbose logging to see detailed information about API requests and responses:

```python
client = FreshRSSAPI(verbose=True)
# Now all API calls will log detailed information using Loguru
```

## API Details

This library interacts with the FreshRSS Fever API, which is a simplified API for mobile access and third-party integrations. The API endpoints are well-documented and provide access to most features of FreshRSS.

For more details on the Fever API, refer to the [official documentation](https://freshrss.github.io/FreshRSS/en/developers/06_Fever_API.html).

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any improvements or bug fixes.

## Acknowledgements

This project was inspired by the need for a simple and reliable Python client for the FreshRSS Fever API. Thanks to the FreshRSS team for their work on this excellent RSS aggregator!

## Contact

For any questions or issues, please open an issue here.
