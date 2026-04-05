"""
GitHub API changelog fetcher for Copilot releases.
Queries github/copilot-language-server-release repo for recent releases.
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os


class ChangelogFetcher:
    """Fetch Copilot CLI changelog from GitHub API."""

    REPO_OWNER = "github"
    REPO_NAME = "copilot-cli"
    API_BASE = "https://api.github.com"

    def __init__(self, days: int = 7):
        """Initialize fetcher with time window (default last 7 days)."""
        self.days = days
        self.github_token = os.getenv("GITHUB_TOKEN")

    def fetch_releases(self) -> List[Dict]:
        """
        Fetch releases from last N days.
        Returns list of dicts with: {version, date, title, notes, url}
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.days)

        url = f"{self.API_BASE}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/releases"
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            releases = response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch releases: {e}")

        # Filter by date and map to structured format
        structured = []
        for release in releases:
            published_at = datetime.fromisoformat(
                release["published_at"].replace("Z", "+00:00")
            ).replace(tzinfo=None)

            if published_at >= cutoff_date:
                structured.append({
                    "version": release["tag_name"],
                    "date": published_at.isoformat(),
                    "title": release.get("name", release["tag_name"]),
                    "notes": release.get("body", ""),
                    "url": release["html_url"],
                    "prerelease": release.get("prerelease", False),
                })

        return sorted(structured, key=lambda x: x["date"], reverse=True)

    def to_json(self, releases: List[Dict]) -> str:
        """Convert releases to JSON string."""
        return json.dumps(releases, indent=2)


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    fetcher = ChangelogFetcher(days=days)
    releases = fetcher.fetch_releases()
    print(fetcher.to_json(releases))
