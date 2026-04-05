"""
Copilot CLI changelog.md parser.
Fetches and parses https://github.com/github/copilot-cli/blob/main/changelog.md
Provides detailed historical context as secondary source.
"""

import re
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class MarkdownChangelogEntry:
    """Structured changelog entry from markdown source."""
    version: str
    date: str
    section: str  # "New", "Fixed", "Improved", "Removed"
    features: List[str]


class MarkdownChangelogParser:
    """Parse Copilot CLI changelog.md for detailed historical context."""

    CHANGELOG_URL = "https://raw.githubusercontent.com/github/copilot-cli/main/changelog.md"

    def fetch_changelog_markdown(self) -> str:
        """
        Fetch raw changelog.md from GitHub.
        Returns raw markdown text or empty string if fetch fails.
        """
        try:
            response = requests.get(self.CHANGELOG_URL, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch changelog.md: {e}")
            return ""

    def parse_changelog_markdown(self, markdown_text: str) -> List[MarkdownChangelogEntry]:
        """
        Parse changelog.md markdown structure.
        Returns list of structured entries: {version, date, section, features[]}

        Structure:
        ## 1.0.18 - 2026-04-04
        - New feature description
        - Another feature

        ## 1.0.17 - 2026-04-03
        ...
        """
        entries = []
        if not markdown_text:
            return entries

        # Split by version headers (## X.X.X - YYYY-MM-DD)
        version_pattern = r"^## ([\d.]+(?:-\d+)?)\s*-\s*(\d{4}-\d{2}-\d{2})"
        lines = markdown_text.split("\n")

        current_version = None
        current_date = None
        current_section = None
        current_features = []

        for line in lines:
            # Check for version header
            version_match = re.match(version_pattern, line.strip())
            if version_match:
                # Save previous entry if exists
                if current_version and current_features:
                    entries.append(
                        MarkdownChangelogEntry(
                            version=current_version,
                            date=current_date,
                            section=current_section or "Features",
                            features=current_features,
                        )
                    )
                current_version = version_match.group(1)
                current_date = version_match.group(2)
                current_section = None
                current_features = []
                continue

            # Check for section headers (bold text at start of line)
            section_match = re.match(r"^\*\*(\w+)\*\*", line.strip())
            if section_match and current_version:
                # Save previous section
                if current_features:
                    entries.append(
                        MarkdownChangelogEntry(
                            version=current_version,
                            date=current_date,
                            section=current_section or "Features",
                            features=current_features,
                        )
                    )
                current_section = section_match.group(1)
                current_features = []
                continue

            # Extract feature bullet points (lines starting with -)
            if line.strip().startswith("- ") and current_version:
                feature = line.strip()[2:].strip()
                if feature:  # Skip empty lines
                    current_features.append(feature)

        # Save final entry
        if current_version and current_features:
            entries.append(
                MarkdownChangelogEntry(
                    version=current_version,
                    date=current_date,
                    section=current_section or "Features",
                    features=current_features,
                )
            )

        return entries

    def to_dict_list(self, entries: List[MarkdownChangelogEntry]) -> List[Dict]:
        """Convert entries to dictionary list for JSON serialization."""
        return [
            {
                "version": entry.version,
                "date": entry.date,
                "section": entry.section,
                "features": entry.features,
                "source": "markdown",
                "authority": 80,  # Markdown is secondary source
            }
            for entry in entries
        ]


if __name__ == "__main__":
    parser = MarkdownChangelogParser()
    raw_md = parser.fetch_changelog_markdown()
    entries = parser.parse_changelog_markdown(raw_md)
    print(f"Parsed {len(entries)} changelog entries from markdown")
    for entry in entries[:3]:
        print(f"  - v{entry.version} ({entry.date}): {len(entry.features)} features in {entry.section}")
