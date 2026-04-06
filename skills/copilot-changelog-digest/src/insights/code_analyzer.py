"""
Code analyzer for detecting patterns in source code.

Scans repository files to identify code patterns that align with
Copilot features:
- Async/await patterns and Promise chains
- Error handling approaches
- Testing patterns
- Code organization and coupling
- Performance patterns
- Debugging approaches
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


class CodeAnalyzer:
    """Analyze source code patterns in a repository."""

    def __init__(self, repo_path: str):
        """Initialize analyzer with repository path."""
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.patterns = {}
        self._file_cache = {}

    def analyze_repository(self) -> Dict:
        """
        Analyze entire repository for patterns.

        Returns:
        {
            "patterns": {
                "async_issues": [{file, lines, snippet}, ...],
                "error_handling": [{file, lines, snippet}, ...],
                "testing": [{file, lines, snippet}, ...],
                "code_organization": [{file, lines, snippet}, ...],
                "performance": [{file, lines, snippet}, ...],
                "debugging": [{file, lines, snippet}, ...],
            },
            "file_patterns": {file: [pattern1, pattern2, ...]},
            "summary": {...}
        }
        """
        results = {
            "async_issues": [],
            "error_handling": [],
            "testing": [],
            "code_organization": [],
            "performance": [],
            "debugging": [],
        }

        file_patterns = defaultdict(list)
        file_count = 0

        # Analyze top files by modification frequency (if chronicle data available)
        # For now, sample recent Python/JS/TS files
        file_extensions = [
            "*.py",
            "*.js",
            "*.ts",
            "*.tsx",
            "*.jsx",
            "*.go",
            "*.rs",
        ]

        files_to_analyze = []
        for ext in file_extensions:
            files_to_analyze.extend(self.repo_path.glob(f"**/{ext}"))
            files_to_analyze.extend(self.repo_path.glob(f"src/**/{ext}"))

        # Limit to most recently modified files
        files_to_analyze = sorted(
            set(files_to_analyze),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:30]  # Top 30 by modification time

        for file_path in files_to_analyze:
            if file_count >= 30:
                break

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative_path = file_path.relative_to(self.repo_path)

                # Analyze different patterns
                async_issues = self._detect_async_issues(
                    content, str(relative_path)
                )
                error_handling = self._detect_error_handling(
                    content, str(relative_path)
                )
                testing = self._detect_testing(content, str(relative_path))
                code_org = self._detect_code_organization(
                    content, str(relative_path)
                )
                perf = self._detect_performance_issues(content, str(relative_path))
                debug = self._detect_debugging_patterns(content, str(relative_path))

                results["async_issues"].extend(async_issues)
                results["error_handling"].extend(error_handling)
                results["testing"].extend(testing)
                results["code_organization"].extend(code_org)
                results["performance"].extend(perf)
                results["debugging"].extend(debug)

                # Track which patterns found in this file
                patterns_found = []
                if async_issues:
                    patterns_found.append("async_issues")
                if error_handling:
                    patterns_found.append("error_handling")
                if testing:
                    patterns_found.append("testing")
                if code_org:
                    patterns_found.append("code_organization")
                if perf:
                    patterns_found.append("performance")
                if debug:
                    patterns_found.append("debugging")

                if patterns_found:
                    file_patterns[str(relative_path)] = patterns_found
                    file_count += 1

            except Exception:
                pass

        return {
            "patterns": results,
            "file_patterns": dict(file_patterns),
            "summary": {
                "files_analyzed": len(files_to_analyze),
                "files_with_patterns": len(file_patterns),
                "async_issues_found": len(results["async_issues"]),
                "error_handling_issues_found": len(results["error_handling"]),
                "testing_issues_found": len(results["testing"]),
                "organization_issues_found": len(results["code_organization"]),
                "performance_issues_found": len(results["performance"]),
                "debugging_patterns_found": len(results["debugging"]),
            },
        }

    def _detect_async_issues(self, content: str, file_path: str) -> List[Dict]:
        """Detect async/await and Promise handling issues."""
        issues = []

        # Promise.all without error handling
        promise_all_pattern = r"Promise\.all\s*\("
        for match in re.finditer(promise_all_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            # Check if followed by .catch or try/catch
            end_pos = min(match.end() + 200, len(content))
            context = content[match.start() : end_pos]
            if ".catch" not in context and "try" not in context:
                issues.append(
                    {
                        "file": file_path,
                        "line": line_num,
                        "pattern": "Promise.all without error guard",
                        "snippet": context[:100],
                        "severity": "high",
                    }
                )

        # Async function without error handling
        async_func_pattern = r"async\s+function|async\s*\("
        for match in re.finditer(async_func_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            # Get function body
            end_pos = min(match.end() + 300, len(content))
            context = content[match.start() : end_pos]
            if "try" not in context and ".catch" not in context:
                issues.append(
                    {
                        "file": file_path,
                        "line": line_num,
                        "pattern": "Async function without error handling",
                        "snippet": context[:100],
                        "severity": "medium",
                    }
                )

        # Unhandled promise rejection (missing await)
        then_pattern = r"\.then\s*\([^)]+\)\s*[;.]"
        for match in re.finditer(then_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            start_pos = max(0, match.start() - 50)
            context = content[start_pos : match.end() + 50]
            if "await" not in context and "return" not in context:
                issues.append(
                    {
                        "file": file_path,
                        "line": line_num,
                        "pattern": "Unhandled promise (missing await/return)",
                        "snippet": context.strip()[:100],
                        "severity": "high",
                    }
                )

        return issues[:3]  # Limit to top 3 per file

    def _detect_error_handling(self, content: str, file_path: str) -> List[Dict]:
        """Detect error handling patterns and issues."""
        issues = []

        # Too many try blocks without proper error context
        try_count = len(re.findall(r"\btry\b", content))
        catch_count = len(re.findall(r"\bcatch\b", content))

        if try_count > 0 and catch_count > 0 and catch_count < try_count * 0.5:
            issues.append(
                {
                    "file": file_path,
                    "line": 1,
                    "pattern": "Incomplete error handling",
                    "snippet": f"File has {try_count} try blocks but only {catch_count} catch blocks",
                    "severity": "medium",
                }
            )

        # Check for empty catch blocks
        empty_catch_pattern = r"catch\s*\([^)]*\)\s*\{\s*\}"
        for match in re.finditer(empty_catch_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                {
                    "file": file_path,
                    "line": line_num,
                    "pattern": "Empty catch block (silently swallowing errors)",
                    "snippet": content[match.start() : match.end()],
                    "severity": "high",
                }
            )

        return issues[:3]

    def _detect_testing(self, content: str, file_path: str) -> List[Dict]:
        """Detect testing patterns and test file information."""
        issues = []

        # Check if file is a test file
        is_test = any(
            pattern in file_path.lower()
            for pattern in ["test", "spec", "__tests__"]
        )

        if is_test:
            # Count test functions
            test_pattern = r"(test|it|describe|suite)\s*\("
            test_count = len(re.findall(test_pattern, content))
            if test_count > 0:
                issues.append(
                    {
                        "file": file_path,
                        "line": 1,
                        "pattern": "Test file with test coverage",
                        "snippet": f"Contains {test_count} test cases",
                        "severity": "info",
                    }
                )
        else:
            # Check if main file lacks tests
            mock_count = len(re.findall(r"jest.mock|unittest.mock", content))
            if mock_count == 0 and len(content) > 500:
                issues.append(
                    {
                        "file": file_path,
                        "line": 1,
                        "pattern": "No test coverage detected",
                        "snippet": "Consider adding unit tests",
                        "severity": "low",
                    }
                )

        return issues[:2]

    def _detect_code_organization(self, content: str, file_path: str) -> List[Dict]:
        """Detect code organization and coupling issues."""
        issues = []

        # Count imports/requires as proxy for coupling
        import_count = len(
            re.findall(
                r"^(?:import|require|from)\s+", content, re.MULTILINE
            )
        )
        code_lines = len([l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")])

        if code_lines > 200 and import_count > 15:
            issues.append(
                {
                    "file": file_path,
                    "line": 1,
                    "pattern": "High coupling (many imports)",
                    "snippet": f"{import_count} imports in {code_lines} lines",
                    "severity": "medium",
                }
            )

        # Check file size
        if code_lines > 500:
            issues.append(
                {
                    "file": file_path,
                    "line": 1,
                    "pattern": "Large file (could be split)",
                    "snippet": f"{code_lines} lines of code",
                    "severity": "low",
                }
            )

        return issues[:2]

    def _detect_performance_issues(self, content: str, file_path: str) -> List[Dict]:
        """Detect performance anti-patterns."""
        issues = []

        # Synchronous file operations
        sync_io_pattern = r"\b(readFileSync|writeFileSync|readSync|writeSync)\b"
        for match in re.finditer(sync_io_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                {
                    "file": file_path,
                    "line": line_num,
                    "pattern": "Synchronous I/O operation",
                    "snippet": match.group(),
                    "severity": "medium",
                }
            )

        # N+1 like patterns (loops with operations)
        loop_pattern = r"\bfor\s*\(|while\s*\(|\.forEach\s*\("
        if len(re.findall(loop_pattern, content)) > 5:
            db_pattern = r"\.query\(|\.find\(|\.get\(|\.fetch\("
            if len(re.findall(db_pattern, content)) > 0:
                issues.append(
                    {
                        "file": file_path,
                        "line": 1,
                        "pattern": "Potential N+1 query pattern",
                        "snippet": f"{len(re.findall(loop_pattern, content))} loops with database operations",
                        "severity": "medium",
                    }
                )

        return issues[:2]

    def _detect_debugging_patterns(self, content: str, file_path: str) -> List[Dict]:
        """Detect debugging approaches used in code."""
        issues = []

        # Count console.log statements
        log_count = len(re.findall(r"console\.log|print\(", content))
        if log_count > 10:
            issues.append(
                {
                    "file": file_path,
                    "line": 1,
                    "pattern": "Heavy debugging via logging",
                    "snippet": f"{log_count} log statements found",
                    "severity": "info",
                }
            )

        # Check for debugger statements
        debugger_pattern = r"\bdebugger\b|pdb\.set_trace|breakpoint\(\)"
        for match in re.finditer(debugger_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                {
                    "file": file_path,
                    "line": line_num,
                    "pattern": "Debugger statement left in code",
                    "snippet": match.group(),
                    "severity": "high",
                }
            )

        return issues[:2]

    def get_files_for_pattern(
        self, pattern_name: str, limit: int = 3
    ) -> List[str]:
        """Get files that contain a specific pattern."""
        analysis = self.analyze_repository()
        files = set()

        for pattern_data in analysis["patterns"].get(pattern_name, []):
            files.add(pattern_data["file"])

        return list(files)[:limit]
