from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
from importlib.util import find_spec


@dataclass(frozen=True)
class Item:
    id: int
    feed_id: int
    title: str
    author: str
    html: str
    url: str
    is_saved: bool
    is_read: bool
    created_on_time: int

    @property
    def readable(self) -> str:
        """Return human readable text content from HTML"""
        # Try to use markdownify if available
        if find_spec("markdownify"):
            from markdownify import markdownify

            return markdownify(self.html, heading_style="ATX").strip()

        # Fallback to BeautifulSoup implementation
        soup = BeautifulSoup(self.html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text and clean up whitespace
        text = soup.get_text(separator=" ")
        # Remove excessive whitespace while preserving paragraphs
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines and join with newlines
        return "\n".join(chunk for chunk in chunks if chunk).strip()

    @property
    def created_datetime(self) -> datetime:
        """Return datetime object from created_on_time timestamp"""
        return datetime.fromtimestamp(self.created_on_time)

    @property
    def id_datetime(self) -> datetime:
        """Return datetime object from id timestamp"""
        return datetime.fromtimestamp(self.id)
