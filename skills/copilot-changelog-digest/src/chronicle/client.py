"""
Chronicle API client for fetching user development patterns.

Interfaces with Copilot's /chronicle API to retrieve:
- Recently modified files (last 7 days)
- Most frequently edited files
- Recent commits with messages and files touched
- Time spent on different areas of codebase
- Common error patterns
- Development workflow patterns
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import time


class ChronicleCache:
    """Simple file-based cache for chronicle data with TTL."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_minutes: int = 30):
        """Initialize cache with optional TTL."""
        if cache_dir is None:
            cache_dir = Path.home() / ".copilot" / "chronicle_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_minutes = ttl_minutes

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if present and not expired."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            # Check TTL
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            if datetime.now() - cached_at > timedelta(minutes=self.ttl_minutes):
                return None

            return data.get("value")
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def set(self, key: str, value: Dict) -> None:
        """Store value in cache with timestamp."""
        cache_path = self._get_cache_path(key)
        cache_data = {"cached_at": datetime.now().isoformat(), "value": value}
        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

    def clear(self) -> None:
        """Clear all cached entries."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class ChronicleClient:
    """Client for Copilot /chronicle API integration."""

    def __init__(self, cache: Optional[ChronicleCache] = None):
        """Initialize chronicle client with optional cache."""
        self.cache = cache or ChronicleCache()
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if /chronicle is available in Copilot CLI."""
        try:
            result = subprocess.run(
                ["copilot", "chronicle", "--version"],
                capture_output=True,
                timeout=5,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def fetch_user_patterns(self, repo_path: str = ".") -> Dict:
        """
        Fetch user development patterns from /chronicle.

        Returns:
        {
            "success": bool,
            "error": Optional[str],
            "recent_files": [{path, last_modified, edits_count}, ...],
            "frequent_files": [{path, edit_count}, ...],
            "recent_commits": [{hash, message, files_touched, timestamp}, ...],
            "time_patterns": {file_path: {hours_spent, last_session}, ...},
            "workflow_patterns": {pattern_name: bool, ...},
            "error_patterns": [pattern_name, ...],
            "focus_areas": [area_name, ...]
        }
        """
        cache_key = f"chronicle:patterns:{Path(repo_path).resolve()}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if not self.available:
            return self._get_fallback_patterns(repo_path)

        try:
            result = self._fetch_from_chronicle(repo_path)
            self.cache.set(cache_key, result)
            return result
        except Exception as e:
            # Graceful degradation: return fallback if API fails
            return self._get_fallback_patterns(repo_path, error_msg=str(e))

    def _fetch_from_chronicle(self, repo_path: str) -> Dict:
        """Fetch actual data from /chronicle API."""
        try:
            # Call copilot chronicle API
            result = subprocess.run(
                ["copilot", "chronicle", "patterns", f"--repo={repo_path}", "--json"],
                capture_output=True,
                timeout=10,
                text=True,
            )

            if result.returncode != 0:
                return self._get_fallback_patterns(
                    repo_path, error_msg=f"Chronicle returned {result.returncode}"
                )

            data = json.loads(result.stdout)
            return {
                "success": True,
                "error": None,
                "recent_files": data.get("recent_files", []),
                "frequent_files": data.get("frequent_files", []),
                "recent_commits": data.get("recent_commits", []),
                "time_patterns": data.get("time_patterns", {}),
                "workflow_patterns": data.get("workflow_patterns", {}),
                "error_patterns": data.get("error_patterns", []),
                "focus_areas": data.get("focus_areas", []),
                "source": "chronicle_api",
            }
        except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            return self._get_fallback_patterns(repo_path, error_msg=str(e))

    def _get_fallback_patterns(
        self, repo_path: str, error_msg: Optional[str] = None
    ) -> Dict:
        """Return fallback patterns when chronicle is unavailable."""
        repo_path = Path(repo_path).resolve()

        # Try to extract some basic patterns from git history if possible
        recent_files = []
        frequent_files = []
        recent_commits = []

        try:
            # Get recent modified files from git
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_path),
                    "log",
                    "--name-only",
                    "--format=%H|%s|%aI",
                    "-20",
                ],
                capture_output=True,
                timeout=5,
                text=True,
            )

            if result.returncode == 0:
                file_counts = {}
                for line in result.stdout.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            commit_hash, message, timestamp = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            recent_commits.append(
                                {
                                    "hash": commit_hash[:8],
                                    "message": message,
                                    "timestamp": timestamp,
                                    "files_touched": [],
                                }
                            )
                    elif line.strip() and "/" in line:
                        file_counts[line.strip()] = file_counts.get(line.strip(), 0) + 1
                        recent_files.append(
                            {
                                "path": line.strip(),
                                "edits_count": file_counts[line.strip()],
                            }
                        )

                # Get most frequent files
                frequent_files = sorted(
                    [
                        {"path": path, "edit_count": count}
                        for path, count in file_counts.items()
                    ],
                    key=lambda x: x["edit_count"],
                    reverse=True,
                )[:10]
        except Exception:
            pass

        return {
            "success": True,
            "error": error_msg,
            "recent_files": recent_files,
            "frequent_files": frequent_files,
            "recent_commits": recent_commits,
            "time_patterns": {},
            "workflow_patterns": {
                "uses_testing": self._detect_testing(repo_path),
                "uses_ci_cd": self._detect_ci_cd(repo_path),
                "uses_linting": self._detect_linting(repo_path),
                "uses_debugging": self._detect_debugging_tools(repo_path),
            },
            "error_patterns": self._extract_error_patterns(recent_commits),
            "focus_areas": self._extract_focus_areas(recent_commits),
            "source": "git_fallback",
        }

    def _detect_testing(self, repo_path: Path) -> bool:
        """Detect if repo uses testing."""
        test_indicators = [
            "test",
            "__tests__",
            "spec",
            "pytest.ini",
            "jest.config",
            "vitest.config",
            ".mocharc",
        ]
        for file_or_dir in repo_path.rglob("*"):
            if any(indicator in file_or_dir.name.lower() for indicator in test_indicators):
                return True
        return False

    def _detect_ci_cd(self, repo_path: Path) -> bool:
        """Detect if repo uses CI/CD."""
        ci_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "Jenkinsfile",
            ".circleci",
        ]
        return any((repo_path / ci_file).exists() for ci_file in ci_files)

    def _detect_linting(self, repo_path: Path) -> bool:
        """Detect if repo uses linting."""
        lint_files = [
            ".eslintrc",
            ".flake8",
            ".pylintrc",
            ".stylelintrc",
            "prettier.config",
        ]
        return any((repo_path / lint_file).exists() for lint_file in lint_files)

    def _detect_debugging_tools(self, repo_path: Path) -> bool:
        """Detect if repo has debugging tools/patterns."""
        debug_indicators = [
            "debugger",
            "pdb",
            "console.log",
            "print(",
            "logger",
        ]
        python_files = list(repo_path.glob("**/*.py"))[:10]
        for py_file in python_files:
            try:
                content = py_file.read_text(errors="ignore")
                if any(indicator in content for indicator in debug_indicators):
                    return True
            except Exception:
                pass
        return False

    def _extract_error_patterns(self, commits: List[Dict]) -> List[str]:
        """Extract common error patterns from commit messages."""
        patterns = []
        error_keywords = [
            "fix",
            "bug",
            "race condition",
            "memory leak",
            "timeout",
            "deadlock",
            "exception",
            "crash",
            "error",
        ]

        for commit in commits:
            message = commit.get("message", "").lower()
            for keyword in error_keywords:
                if keyword in message and keyword not in patterns:
                    patterns.append(keyword)

        return patterns[:5]

    def _extract_focus_areas(self, commits: List[Dict]) -> List[str]:
        """Extract focus areas from commit messages."""
        areas = []
        area_keywords = [
            "api",
            "database",
            "frontend",
            "ui",
            "performance",
            "security",
            "auth",
            "logging",
            "caching",
            "deployment",
        ]

        for commit in commits:
            message = commit.get("message", "").lower()
            for keyword in area_keywords:
                if keyword in message and keyword not in areas:
                    areas.append(keyword)

        return areas[:5]

    def get_personalization_context(self, repo_path: str = ".") -> Dict:
        """
        Get personalization context suitable for enhancing use cases.

        Returns focused data for linking changelog features to user's actual work:
        {
            "recent_files": [file1, file2, ...] (top 3),
            "frequent_files": [file1, file2, ...] (top 3),
            "workflow_patterns": {pattern: True/False},
            "error_patterns": [pattern1, pattern2, ...],
            "focus_areas": [area1, area2, ...],
            "available": bool
        }
        """
        patterns = self.fetch_user_patterns(repo_path)

        return {
            "recent_files": [f.get("path") for f in patterns.get("recent_files", [])][
                :3
            ],
            "frequent_files": [f.get("path") for f in patterns.get("frequent_files", [])][
                :3
            ],
            "workflow_patterns": patterns.get("workflow_patterns", {}),
            "error_patterns": patterns.get("error_patterns", []),
            "focus_areas": patterns.get("focus_areas", []),
            "available": patterns.get("success", False),
            "source": patterns.get("source", "unknown"),
        }
