"""
Repository analyzer: detect tech stack, parse dependencies, analyze recent commits.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set


class RepoAnalyzer:
    """Analyze repository structure and tech stack."""

    # File signatures for tech detection
    TECH_SIGNATURES = {
        "node": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
        "python": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "php": ["composer.json", "composer.lock"],
        "java": ["pom.xml", "build.gradle", "gradle.properties"],
        "csharp": ["*.csproj", "*.sln"],
        "typescript": ["tsconfig.json"],
        "react": ["package.json"],  # combined with node
        "vue": ["package.json"],
        "angular": ["angular.json", "package.json"],
        "nextjs": ["next.config.js", "package.json"],
    }

    def __init__(self, repo_path: str = "."):
        """Initialize analyzer with repo path."""
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repo path does not exist: {repo_path}")

    def analyze(self) -> Dict:
        """Run full analysis and return structured context."""
        return {
            "path": str(self.repo_path),
            "tech_stack": self._detect_tech_stack(),
            "dependencies": self._parse_dependencies(),
            "recent_commits": self._analyze_recent_commits(),
            "file_structure": self._analyze_file_structure(),
        }

    def _detect_tech_stack(self) -> List[str]:
        """Detect technologies in use."""
        detected = set()

        for tech, signatures in self.TECH_SIGNATURES.items():
            for sig in signatures:
                # Handle glob patterns like *.csproj
                if "*" in sig:
                    pattern = sig.replace("*", "")
                    if any(self.repo_path.glob(f"*{pattern}")):
                        detected.add(tech)
                elif (self.repo_path / sig).exists():
                    detected.add(tech)

        return sorted(list(detected))

    def _parse_dependencies(self) -> Dict:
        """Extract key dependencies from various package managers."""
        deps = {}

        # Parse package.json (Node/TypeScript)
        pkg_json = self.repo_path / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    pkg_data = json.load(f)
                    deps["npm"] = {
                        "dependencies": list(
                            (pkg_data.get("dependencies") or {}).keys()
                        )[:10],  # Top 10
                        "devDependencies": list(
                            (pkg_data.get("devDependencies") or {}).keys()
                        )[:5],
                    }
            except Exception:
                pass

        # Parse requirements.txt (Python)
        req_txt = self.repo_path / "requirements.txt"
        if req_txt.exists():
            try:
                with open(req_txt) as f:
                    packages = [
                        line.split("==")[0].split(">")[0].strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
                    deps["python"] = packages[:10]  # Top 10
            except Exception:
                pass

        # Parse go.mod (Go)
        go_mod = self.repo_path / "go.mod"
        if go_mod.exists():
            try:
                with open(go_mod) as f:
                    content = f.read()
                    lines = [
                        l.split()[0] for l in content.split("\n") if "require" in l
                    ]
                    deps["go"] = lines[:10]
            except Exception:
                pass

        return deps

    def _analyze_recent_commits(self) -> List[Dict]:
        """Analyze last 10-20 commits to understand activity patterns."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.repo_path),
                    "log",
                    "--oneline",
                    "-20",
                    "--pretty=format:%H|%an|%ai|%s",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    })

            return commits
        except Exception:
            return []

    def _analyze_file_structure(self) -> Dict:
        """Analyze file types and distribution."""
        file_counts = {}
        extensions = set()

        for file_path in self.repo_path.rglob("*"):
            # Skip hidden and common non-code directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if any(
                skip in file_path.parts
                for skip in ["node_modules", "venv", "__pycache__", ".git", "dist", "build"]
            ):
                continue

            if file_path.is_file():
                ext = file_path.suffix or "no_extension"
                extensions.add(ext)
                file_counts[ext] = file_counts.get(ext, 0) + 1

        # Top file types
        top_types = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "top_file_types": [{"extension": ext, "count": count} for ext, count in top_types],
            "total_file_types": len(extensions),
        }

    def to_json(self) -> str:
        """Convert analysis to JSON."""
        return json.dumps(self.analyze(), indent=2)


if __name__ == "__main__":
    import sys

    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    analyzer = RepoAnalyzer(repo_path)
    print(analyzer.to_json())
