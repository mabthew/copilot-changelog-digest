"""
Crawl docs.github.com/en/copilot for recent updates.
Extracts page titles, URLs, and last-updated timestamps to identify
recently changed documentation relevant to Copilot CLI.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .cache import DocsCache


class DocsCrawler:
    """Crawl Copilot documentation from docs.github.com."""

    # Base URLs for documentation crawling
    DOCS_BASE = "https://docs.github.com/en/copilot"
    GITHUB_DOCS_API = "https://docs.github.com"

    # Request settings
    REQUEST_TIMEOUT = 10
    REQUEST_DELAY = 1.0  # Seconds between requests (respect robots.txt)
    USER_AGENT = "Copilot-Changelog-Digest/1.0"

    def __init__(self, days: int = 7, cache: Optional[DocsCache] = None):
        """
        Initialize docs crawler.

        Args:
            days: Number of days to look back for recent changes
            cache: DocsCache instance for caching results
        """
        self.days = days
        self.cutoff_date = datetime.utcnow() - timedelta(days=days)
        self.cache = cache or DocsCache()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with appropriate headers."""
        session = requests.Session()
        session.headers.update({"User-Agent": self.USER_AGENT})
        return session

    def fetch_copilot_docs_index(self) -> Optional[List[Dict]]:
        """
        Fetch the Copilot documentation index page to find all relevant docs.
        Returns list of dicts with: {title, url, description}
        """
        # Check cache first
        cache_key = "copilot_docs_index"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self.session.get(
                self.DOCS_BASE, timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch docs index: {e}")
            return None

        # Parse index page to find documentation links
        docs = self._parse_docs_index(response.text)

        # Cache the result
        if docs:
            self.cache.set(cache_key, docs, {"source": "docs_index"})

        return docs

    def _parse_docs_index(self, html: str) -> List[Dict]:
        """
        Parse the documentation index HTML to extract documentation links.
        Looks for article links and navigation items related to Copilot CLI.
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = []

        # Find all article/documentation links on the page
        # docs.github.com typically uses 'a' tags with specific classes
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Filter for Copilot-related docs
            if not href.startswith("/en/copilot"):
                continue

            # Skip certain paths
            if any(
                skip in href
                for skip in ["/assets/", "/search", "/contribute", "/release-notes"]
            ):
                continue

            full_url = urljoin(self.GITHUB_DOCS_API, href)
            docs.append(
                {
                    "title": text or href,
                    "url": full_url,
                    "path": href,
                    "description": "",
                }
            )

        # Deduplicate by URL
        seen = set()
        unique_docs = []
        for doc in docs:
            if doc["url"] not in seen:
                seen.add(doc["url"])
                unique_docs.append(doc)

        return unique_docs

    def fetch_doc_page(self, url: str) -> Optional[Dict]:
        """
        Fetch a single documentation page and extract metadata.
        Returns dict with: {title, url, last_updated, content_preview}
        """
        try:
            response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            time.sleep(self.REQUEST_DELAY)  # Rate limiting
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch doc page {url}: {e}")
            return None

        return self._parse_doc_page(response.text, url)

    def _parse_doc_page(self, html: str, url: str) -> Dict:
        """
        Parse a documentation page to extract metadata.
        Looks for title, last-updated info, and first paragraph of content.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title (usually in h1 or page title meta tag)
        title = None
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        if not title:
            title_tag = soup.find("meta", {"property": "og:title"})
            if title_tag:
                title = title_tag.get("content", "")

        # Try to find last-updated timestamp
        # docs.github.com typically includes this in page metadata or footer
        last_updated = None
        updated_text = soup.find(
            ["span", "p"], string=lambda s: s and "updated" in s.lower()
        )
        if updated_text:
            text = updated_text.get_text(strip=True)
            # Try to parse common date formats (this is basic; may need refinement)
            try:
                # Look for ISO dates or "Last updated: ..."
                import re

                date_match = re.search(
                    r"(\d{4}-\d{2}-\d{2}|\w+\s+\d{1,2},\s+\d{4})", text
                )
                if date_match:
                    last_updated = date_match.group(1)
            except Exception:
                pass

        # Extract content preview (first paragraph or first non-empty text)
        content_preview = ""
        for p in soup.find_all("p", limit=3):
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                content_preview = text[:200]
                break

        return {
            "title": title or url,
            "url": url,
            "last_updated": last_updated,
            "content_preview": content_preview,
            "fetched_at": datetime.utcnow().isoformat(),
        }

    def crawl_recent_docs(
        self, docs_list: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Crawl all Copilot docs and identify recently updated ones.
        Returns list of dicts with: {title, url, last_updated, description, source, authority}
        """
        if docs_list is None:
            docs_list = self.fetch_copilot_docs_index()
            if not docs_list:
                return []

        recent_docs = []

        # Limit to first 5 docs to avoid long crawl times
        # (In production, could use robots.txt crawl-delay or implement proper sitemap parsing)
        for doc in docs_list[:5]:
            # Skip if doc looks like a placeholder
            if not doc.get("url"):
                continue

            # Fetch page details with explicit timeout handling
            try:
                page_info = self.fetch_doc_page(doc["url"])
                if not page_info:
                    continue

                # Try to determine if recently updated
                # (This is heuristic-based since GitHub doesn't expose last-modified dates easily)
                is_recent = self._is_recent(page_info.get("last_updated"))

                if is_recent or not page_info.get("last_updated"):
                    # Include all docs (with or without clear update date)
                    # as we want to capture documentation that's relevant
                    recent_docs.append(
                        {
                            "title": page_info["title"],
                            "url": page_info["url"],
                            "description": page_info.get("content_preview", ""),
                            "last_updated": page_info.get("last_updated"),
                            "fetched_at": page_info.get("fetched_at"),
                            "category": "Documentation",
                            "source": "docs.github.com",
                            "authority": 60,  # Authority: 60 for docs (less authoritative than releases/markdown)
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to process doc {doc.get('url')}: {e}")
                continue

        return recent_docs

    def _is_recent(self, date_str: Optional[str]) -> bool:
        """Check if date string indicates recent update (within cutoff_date)."""
        if not date_str:
            return False

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj >= self.cutoff_date
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    def get_cached_docs(self) -> Optional[List[Dict]]:
        """Return cached docs list without fetching."""
        return self.cache.get("copilot_docs_index")
