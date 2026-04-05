"""
Copilot CLI changelog fetcher - multi-source.
Fetches from:
1. GitHub releases API (github/copilot-cli) - primary source (authority: 100)
2. changelog.md markdown - secondary source (authority: 80)
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from .markdown_parser import MarkdownChangelogParser


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
        Returns list of dicts with: {version, date, title, notes, url, source, authority}
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
                    "source": "api",
                    "authority": 100,  # Primary source
                })

        return sorted(structured, key=lambda x: x["date"], reverse=True)

    def fetch_changelog_markdown(self) -> List[Dict]:
        """
        Fetch and parse changelog.md for enrichment.
        Returns list of dicts with: {version, date, section, features, source, authority}
        """
        parser = MarkdownChangelogParser()
        raw_md = parser.fetch_changelog_markdown()
        entries = parser.parse_changelog_markdown(raw_md)
        return parser.to_dict_list(entries)

    def merge_sources(self, api_releases: List[Dict], markdown_entries: List[Dict]) -> List[Dict]:
        """
        Merge API releases with markdown entries.
        - Keep API releases as primary
        - Add markdown as enrichment detail
        - Deduplicate by version matching
        Returns merged list with all sources represented.
        """
        # Create version map for markdown entries
        markdown_by_version = {}
        for entry in markdown_entries:
            version = entry["version"]
            if version not in markdown_by_version:
                markdown_by_version[version] = []
            markdown_by_version[version].append(entry)

        # Enrich API releases with markdown details
        merged = []
        for release in api_releases:
            release_copy = release.copy()
            
            # Try to match and enrich with markdown
            version = release["version"].lstrip("v")  # Remove 'v' prefix for matching
            if version in markdown_by_version:
                # Merge markdown details
                for md_entry in markdown_by_version[version]:
                    merged.append({
                        **release_copy,
                        "markdown_details": md_entry["features"],
                        "markdown_section": md_entry["section"],
                    })
                # Remove from markdown map so we don't duplicate
                del markdown_by_version[version]
            else:
                merged.append(release_copy)

        # Add markdown-only entries (versions not in API, for historical context)
        for version, entries in markdown_by_version.items():
            for entry in entries:
                merged.append(entry)

        return sorted(merged, key=lambda x: x["date"], reverse=True)

    def fetch_combined(self) -> List[Dict]:
        """
        Fetch and merge all sources (API + markdown).
        Returns unified changelog list with source attribution.
        """
        try:
            api_releases = self.fetch_releases()
        except Exception as e:
            print(f"Warning: API fetch failed: {e}, continuing with markdown only")
            api_releases = []

        try:
            markdown_entries = self.fetch_changelog_markdown()
        except Exception as e:
            print(f"Warning: Markdown fetch failed: {e}, continuing with API only")
            markdown_entries = []

        if api_releases and markdown_entries:
            return self.merge_sources(api_releases, markdown_entries)
        elif api_releases:
            return api_releases
        elif markdown_entries:
            return markdown_entries
        else:
            return []

    def to_json(self, releases: List[Dict]) -> str:
        """Convert releases to JSON string."""
        return json.dumps(releases, indent=2)


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    fetcher = ChangelogFetcher(days=days)
    releases = fetcher.fetch_releases()
    print(fetcher.to_json(releases))
