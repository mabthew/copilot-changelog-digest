"""
Pattern matcher for linking changelog features to user code patterns.

Maps Copilot features to code patterns found in the repository,
with real time savings estimates based on user workflow data.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re


class PatternMatcher:
    """Link changelog features to user-specific code patterns."""

    def __init__(
        self,
        code_analysis: Dict,
        chronicle_context: Dict,
        repo_context: Dict,
    ):
        """Initialize with analysis results."""
        self.code_analysis = code_analysis
        self.chronicle_context = chronicle_context
        self.repo_context = repo_context

        # Map features to patterns they address
        self.feature_pattern_mapping = {
            "Critic Agent": [
                "async_issues",
                "error_handling",
                "debugging",
                "code_organization",
            ],
            "Agentic Workflows": ["code_organization", "async_issues"],
            "Improved Debugging": ["debugging", "error_handling"],
            "Smart Indexing": ["code_organization", "performance"],
            "Enhanced Completions": [
                "testing",
                "error_handling",
                "code_organization",
            ],
            "Performance Tools": ["performance", "async_issues"],
            "Testing Assistant": ["testing"],
            "Refactoring Guide": ["code_organization"],
        }

    def match_feature_to_patterns(self, feature: Dict) -> Dict:
        """
        Match a changelog feature to user code patterns.

        Returns:
        {
            "feature": feature_title,
            "matched_patterns": [pattern_matches],
            "affected_files": [file_paths],
            "estimated_time_saved_per_week": X,
            "severity_of_issue": "high/medium/low",
            "workflow_impact": "high/medium/low",
            "confidence": 0.0-1.0,
            "reasoning": "why this matters"
        }
        """
        feature_title = feature.get("title", "")
        description = feature.get("description", "").lower()

        # Find relevant patterns for this feature
        relevant_patterns = self._find_relevant_patterns(feature_title, description)

        # Get affected files
        affected_files = self._get_affected_files(relevant_patterns)

        # Estimate time savings
        time_saved = self._estimate_time_savings(relevant_patterns, affected_files)

        # Determine severity and impact
        severity = self._assess_pattern_severity(relevant_patterns)
        impact = self._assess_workflow_impact(relevant_patterns, time_saved)
        confidence = self._calculate_confidence(relevant_patterns, affected_files)

        return {
            "feature": feature_title,
            "matched_patterns": relevant_patterns,
            "affected_files": affected_files,
            "estimated_time_saved_per_week": time_saved,
            "severity_of_issue": severity,
            "workflow_impact": impact,
            "confidence": confidence,
            "reasoning": self._generate_reasoning(
                feature_title, relevant_patterns, affected_files, time_saved
            ),
        }

    def _find_relevant_patterns(self, feature_title: str, description: str) -> List[str]:
        """Find code patterns relevant to this feature."""
        relevant = []

        # Check feature-to-pattern mapping
        for mapped_feature, patterns in self.feature_pattern_mapping.items():
            if mapped_feature.lower() in feature_title.lower():
                relevant.extend(patterns)
                break

        # Fuzzy matching on description
        description_keywords = {
            "async": ["async_issues"],
            "error": ["error_handling"],
            "test": ["testing"],
            "debug": ["debugging"],
            "performance": ["performance"],
            "refactor": ["code_organization"],
            "code quality": ["code_organization", "error_handling"],
            "bug": ["error_handling", "debugging"],
            "promise": ["async_issues"],
            "concurrent": ["async_issues"],
            "workflow": ["code_organization"],
        }

        for keyword, patterns in description_keywords.items():
            if keyword in description:
                relevant.extend(patterns)

        # Remove duplicates, maintain order
        return list(dict.fromkeys(relevant))

    def _get_affected_files(self, patterns: List[str]) -> List[str]:
        """Get files affected by these patterns."""
        affected = set()
        file_patterns = self.code_analysis.get("file_patterns", {})

        for file_path, file_pattern_list in file_patterns.items():
            if any(p in file_pattern_list for p in patterns):
                # Clean up worktree paths (.claude/worktrees/*/...)
                clean_path = self._clean_worktree_path(file_path)
                affected.add(clean_path)

        # Return top files by frequency
        return sorted(list(affected))[:3]

    def _clean_worktree_path(self, file_path: str) -> str:
        """Remove .claude/worktrees prefix from paths."""
        if ".claude/worktrees/" in file_path:
            # Extract everything after the worktree directory
            parts = file_path.split(".claude/worktrees/")
            if len(parts) > 1:
                # Skip the worktree name and return the rest
                after_worktree = parts[1]
                # Remove the worktree name (first path component)
                path_parts = after_worktree.split("/", 1)
                if len(path_parts) > 1:
                    return path_parts[1]
        return file_path

    def _estimate_time_savings(self, patterns: List[str], affected_files: List[str]) -> float:
        """Estimate time savings per week based on pattern severity and frequency."""
        if not patterns or not affected_files:
            return 0.0

        # Base time estimate per file with issues
        base_time_per_file = {
            "async_issues": 2.0,  # 2 hours per week debugging async issues
            "error_handling": 1.5,
            "testing": 1.0,
            "debugging": 2.5,
            "performance": 1.5,
            "code_organization": 1.0,
        }

        # Count issues by pattern
        pattern_issues = {}
        for pattern in patterns:
            pattern_issues[pattern] = len(
                self.code_analysis.get("patterns", {}).get(pattern, [])
            )

        # Calculate total time
        total_time = 0.0
        for pattern, issue_count in pattern_issues.items():
            base = base_time_per_file.get(pattern, 0.5)
            # More issues = more time spent on this area
            total_time += base * (0.5 + issue_count * 0.15)

        # Adjust based on chronicle workflow patterns
        workflow_patterns = self.chronicle_context.get("workflow_patterns", {})
        if workflow_patterns.get("uses_debugging"):
            total_time *= 1.2  # 20% more time spent if heavy debugging

        # Feature typically saves 10-30% of time spent on these tasks
        time_saved = total_time * 0.2  # Conservative 20% savings estimate

        return round(time_saved, 1)

    def _assess_pattern_severity(self, patterns: List[str]) -> str:
        """Assess overall severity of patterns found."""
        high_severity_patterns = [
            "async_issues",
            "error_handling",
            "debugging",
        ]
        medium_severity_patterns = ["performance", "code_organization"]

        if any(p in high_severity_patterns for p in patterns):
            return "high"
        elif any(p in medium_severity_patterns for p in patterns):
            return "medium"
        else:
            return "low"

    def _assess_workflow_impact(self, patterns: List[str], time_saved: float) -> str:
        """Assess overall workflow impact."""
        if time_saved >= 2.0:
            return "high"
        elif time_saved >= 1.0:
            return "medium"
        else:
            return "low"

    def _calculate_confidence(
        self, patterns: List[str], affected_files: List[str]
    ) -> float:
        """Calculate confidence score (0.0-1.0) for this match."""
        # Confidence increases with:
        # - Number of patterns matched
        # - Number of affected files
        # - Severity of issues

        confidence = 0.5  # Base confidence

        # Add confidence for each matched pattern
        confidence += len(patterns) * 0.15

        # Add confidence for each affected file
        confidence += len(affected_files) * 0.1

        # Cap at 1.0
        return min(confidence, 1.0)

    def _generate_reasoning(
        self,
        feature_title: str,
        patterns: List[str],
        affected_files: List[str],
        time_saved: float,
    ) -> str:
        """Generate human-readable reasoning for this match."""
        if not patterns:
            return f"{feature_title} may provide workflow improvements."

        pattern_descriptions = {
            "async_issues": "Promise/async handling issues",
            "error_handling": "error handling gaps",
            "testing": "test coverage",
            "debugging": "heavy manual debugging",
            "performance": "performance bottlenecks",
            "code_organization": "code organization challenges",
        }

        pattern_names = [pattern_descriptions.get(p, p) for p in patterns[:2]]
        file_info = (
            f" in {len(affected_files)} files" if affected_files else ""
        )

        time_info = (
            f" Potential to save ~{time_saved} hours per week."
            if time_saved > 0
            else ""
        )

        return (
            f"{feature_title} directly addresses {' and '.join(pattern_names)}"
            f"{file_info}.{time_info}"
        )
