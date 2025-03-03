from freshrss_api import FreshRSSAPI
import fire

def freshrss_client(
    host: str,
    username: str,
    password: str,
    verify_ssl=False,
):
    """
    FreshRSS API client.
    
    Args:
        host: FreshRSS host URL
        username: FreshRSS username
        password: FreshRSS password
        verify_ssl: Whether to verify SSL certificates
    """
    inst = FreshRSSAPI(
        host=host,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
    )

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
