"""
Fleet Task A: Fetch Copilot changelog.
To be executed as a parallel /fleet task.
"""

import json
import sys
from src.changelog.fetcher import ChangelogFetcher


def run_task(days: int = 7) -> str:
    """
    Execute Fleet Task A: Fetch changelog.
    Returns JSON string with changelog data.
    """
    try:
        fetcher = ChangelogFetcher(days=days)
        releases = fetcher.fetch_releases()
        return json.dumps({
            "success": True,
            "task": "fetch-changelog",
            "data": releases,
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
