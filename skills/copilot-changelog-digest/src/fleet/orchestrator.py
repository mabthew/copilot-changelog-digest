"""
Fleet orchestrator: launches 3 parallel tasks and syncs results.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


class FleetOrchestrator:
    """Orchestrate parallel /fleet task execution and result syncing."""

    def __init__(self, repo_path: str = ".", days: int = 7):
        """Initialize orchestrator with repo path and time window."""
        self.repo_path = repo_path
        self.days = days
        self.src_dir = Path(__file__).parent.parent

    def run_parallel_tasks(self) -> Dict:
        """
        Launch 3 parallel fleet tasks:
        - Task A: Fetch changelog
        - Task B: Analyze repo
        - Task C: Retrieve user context
        
        Returns merged results.
        """
        # Try to use /fleet for parallel execution
        fleet_results = self._try_fleet_execution()

        # Fallback: run sequentially
        if not fleet_results:
            fleet_results = self._sequential_execution()

        return self._sync_results(fleet_results)

    def _try_fleet_execution(self) -> Optional[Dict]:
        """
        Attempt to use /fleet for parallel execution.
        Falls back to None if /fleet unavailable.
        """
        try:
            # This is a placeholder - actual /fleet integration depends on
            # Copilot's /fleet API availability
            # For now, we'll use sequential execution as fallback
            return None
        except Exception:
            return None

    def _sequential_execution(self) -> Dict:
        """
        Execute 3 tasks sequentially as fallback.
        This is used when /fleet is unavailable.
        """
        results = {
            "task_a": self._run_task_a(),
            "task_b": self._run_task_b(),
            "task_c": self._run_task_c(),
        }
        return results

    def _run_task_a(self) -> Dict:
        """Run Fleet Task A: Fetch changelog."""
        try:
            # Import and run directly
            from src.fleet.task_changelog import run_task

            output = run_task(self.days)
            return json.loads(output)
        except Exception as e:
            return {
                "success": False,
                "task": "fetch-changelog",
                "error": str(e),
            }

    def _run_task_b(self) -> Dict:
        """Run Fleet Task B: Analyze repository."""
        try:
            from src.fleet.task_repo_analyzer import run_task

            output = run_task(self.repo_path)
            return json.loads(output)
        except Exception as e:
            return {
                "success": False,
                "task": "analyze-repo",
                "error": str(e),
            }

    def _run_task_c(self) -> Dict:
        """Run Fleet Task C: Retrieve user context."""
        try:
            from src.fleet.task_user_context import run_task

            output = run_task()
            return json.loads(output)
        except Exception as e:
            return {
                "success": False,
                "task": "retrieve-user-context",
                "error": str(e),
            }

    def _sync_results(self, task_results: Dict) -> Dict:
        """
        Merge results from 3 parallel tasks into unified context object.
        Validates data completeness before returning.
        """
        changelog_data = task_results.get("task_a", {}).get("data", [])
        repo_data = task_results.get("task_b", {}).get("data", {})
        user_context = task_results.get("task_c", {}).get("data", {})

        # Check for errors
        all_successful = all(
            task_results.get(f"task_{letter}", {}).get("success", False)
            for letter in ["a", "b", "c"]
        )

        synced = {
            "timestamp": self._get_timestamp(),
            "repo_path": self.repo_path,
            "time_window_days": self.days,
            "all_tasks_successful": all_successful,
            "changelog": changelog_data,
            "repo_context": repo_data,
            "user_context": user_context,
            "task_results": task_results,  # Raw results for debugging
        }

        return synced

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def to_json(self, synced_data: Dict) -> str:
        """Convert synced results to JSON."""
        return json.dumps(synced_data, indent=2)


if __name__ == "__main__":
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    orchestrator = FleetOrchestrator(repo_path, days)
    results = orchestrator.run_parallel_tasks()
    print(orchestrator.to_json(results))
