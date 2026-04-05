"""
Parse Copilot changelog: extract features from release notes markdown.
"""

import re
import json
from typing import List, Dict, Optional


class ChangelogParser:
    """Parse structured changelog data from release notes."""

    # Keywords that indicate feature categories
    FEATURE_KEYWORDS = {
        "performance": [
            "faster",
            "speed",
            "performance",
            "optimiz",
            "latency",
            "throughput",
        ],
        "debugging": [
            "debug",
            "breakpoint",
            "inspect",
            "diagnos",
            "error",
            "trace",
        ],
        "refactoring": [
            "refactor",
            "restructure",
            "reorganize",
            "modernize",
            "simplify",
        ],
        "testing": [
            "test",
            "unittest",
            "assert",
            "coverage",
            "fixture",
            "mock",
        ],
        "typing": [
            "type",
            "type.*hint",
            "type.*check",
            "typing",
            "generic",
            "interface",
        ],
        "security": [
            "security",
            "vulnerab",
            "encrypt",
            "auth",
            "auth.*",
            "permission",
        ],
        "api": ["api", "endpoint", "rest", "graphql", "client"],
        "ui_ux": ["ui", "ux", "interface", "layout", "visual", "design"],
    }

    def __init__(self):
        """Initialize parser."""
        pass

    def parse_releases(self, releases: List[Dict]) -> List[Dict]:
        """
        Parse list of release objects into structured features.
        Returns list of feature objects with title, description, category, impact_keywords.
        """
        features = []

        for release in releases:
            # Use title or notes
            feature_text = (
                release.get("notes") or release.get("title") or release.get("version")
            )
            if not feature_text:
                continue

            parsed = self._parse_single_feature(feature_text, release)
            if parsed:
                features.append(parsed)

        return features

    def _parse_single_feature(self, text: str, release: Dict) -> Optional[Dict]:
        """Parse a single release/feature into structured form."""
        # Extract first line as title
        lines = text.strip().split("\n")
        title = lines[0][:100]  # First 100 chars

        # Extract description (first 300 chars of body)
        description = "\n".join(lines[1:])[:300]

        # Detect category keywords
        combined_text = (title + " " + description).lower()
        categories = []
        keywords_found = []

        for category, keywords in self.FEATURE_KEYWORDS.items():
            for keyword in keywords:
                if re.search(keyword, combined_text):
                    if category not in categories:
                        categories.append(category)
                    if keyword not in keywords_found:
                        keywords_found.append(keyword)

        return {
            "version": release.get("version"),
            "date": release.get("date"),
            "title": title,
            "description": description,
            "url": release.get("url"),
            "categories": categories if categories else ["general"],
            "impact_keywords": keywords_found,
            "prerelease": release.get("prerelease", False),
        }

    def extract_impact_summary(self, features: List[Dict]) -> Dict:
        """Extract summary of features by category."""
        summary = {}

        for feature in features:
            for category in feature.get("categories", []):
                if category not in summary:
                    summary[category] = []
                summary[category].append({
                    "title": feature["title"],
                    "version": feature["version"],
                })

        return summary

    def to_json(self, features: List[Dict]) -> str:
        """Convert features to JSON."""
        return json.dumps(features, indent=2)


if __name__ == "__main__":
    import sys

    # Test: read changelog JSON and parse
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            changelog = json.load(f)
            parser = ChangelogParser()
            features = parser.parse_releases(changelog)
            print(parser.to_json(features))
