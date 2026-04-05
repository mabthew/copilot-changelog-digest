"""
Fleet Task B: Analyze repository.
To be executed as a parallel /fleet task.
"""

import json
import sys
from src.repo_analyzer.detector import RepoAnalyzer


def run_task(repo_path: str = ".") -> str:
    """
    Execute Fleet Task B: Analyze repository.
    Returns JSON string with repo context data.
    """
    try:
        analyzer = RepoAnalyzer(repo_path)
        analysis = analyzer.analyze()
        return json.dumps({
            "success": True,
            "task": "analyze-repo",
            "data": analysis,
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "task": "analyze-repo",
            "error": str(e),
        })


if __name__ == "__main__":
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = run_task(repo_path)
    print(result)
