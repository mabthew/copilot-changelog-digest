"""
Fleet Task A: Fetch Copilot changelog from multiple sources.
To be executed as a parallel /fleet task.
"""

import json
import sys
from src.changelog.fetcher import ChangelogFetcher


def run_task(days: int = 7) -> str:
    """
    Execute Fleet Task A: Fetch changelog from all sources.
    - GitHub Releases API (authority: 100%)
    - changelog.md (authority: 80%)
    - docs.github.com (authority: 60%)
    
    Returns JSON string with merged changelog data.
    """
    try:
        fetcher = ChangelogFetcher(days=days)
        # Use fetch_combined to get all 3 sources merged
        releases = fetcher.fetch_combined()
        return json.dumps({
            "success": True,
            "task": "fetch-changelog",
            "data": releases,
            "sources_included": ["api", "markdown", "docs"],
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "task": "fetch-changelog",
            "error": str(e),
        })


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    result = run_task(days)
    print(result)
