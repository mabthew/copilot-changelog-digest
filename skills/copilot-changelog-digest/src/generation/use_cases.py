"""
Generate grounded use cases: Create actionable workflow improvements from repo code.

Enhanced with /chronicle integration and code analysis for repository-grounded,
user-specific examples and time estimates.
"""

import json
from typing import List, Dict, Optional
import os
from pathlib import Path


class UseCaseGenerator:
    """Generate workflow-focused use cases grounded in actual repo code."""

    def __init__(
        self,
        repo_path: str,
        repo_context: Dict,
        code_analysis: Optional[Dict] = None,
        chronicle_context: Optional[Dict] = None,
        pattern_matcher: Optional[object] = None,
    ):
        """Initialize generator with repo path and context."""
        self.repo_path = Path(repo_path).resolve()
        self.repo_context = repo_context
        self.tech_stack = repo_context.get("tech_stack", [])
        self.code_analysis = code_analysis or {}
        self.chronicle_context = chronicle_context or {}
        self.pattern_matcher = pattern_matcher

    def generate_use_cases(
        self, features: List[Dict], top_n: int = 5
    ) -> List[Dict]:
        """
        For top-N features, generate actionable use cases grounded in repo.
        Returns features augmented with use_case field.
        """
        # Take top N by score
        top_features = features[:top_n]

        enriched = []
        for feature in top_features:
            use_case = self._generate_single_use_case(feature)
            feature_with_usecase = feature.copy()
            feature_with_usecase["use_case"] = use_case
            enriched.append(feature_with_usecase)

        return enriched

    def _generate_single_use_case(self, feature: Dict) -> Dict:
        """Generate a use case for a single feature."""
        title = feature.get("title", "")
        description = feature.get("description", "")
        categories = feature.get("categories", [])

        # Template-based use case generation based on category
        use_case = {
            "headline": self._generate_headline(feature),
            "context": self._generate_context(feature),
            "code_example": self._find_code_example(feature),
            "workflow_improvement": self._generate_improvement_statement(feature),
            "estimated_impact": self._estimate_impact(feature),
            "why_this_matters_to_you": self._generate_personalized_impact(feature),
        }

        return use_case

    def _generate_headline(self, feature: Dict) -> str:
        """Generate a headline for the use case."""
        title = feature.get("title", "")
        categories = feature.get("categories", [])

        # Create a "how this helps YOU" headline
        if "performance" in categories:
            return f"Speed up your workflow with {title}"
        elif "debugging" in categories:
            return f"Debug faster with {title}"
        elif "refactoring" in categories:
            return f"Refactor safely with {title}"
        elif "testing" in categories:
            return f"Test more thoroughly with {title}"
        else:
            return f"Improve your workflow with {title}"

    def _generate_context(self, feature: Dict) -> str:
        """Generate context explaining why this feature matters."""
        categories = feature.get("categories", [])
        tech_stack = self.tech_stack

        context_templates = {
            "performance": f"For a {', '.join(tech_stack)} project, this can significantly reduce build/run times.",
            "debugging": f"When debugging {', '.join(tech_stack)} code, this feature helps you identify issues faster.",
            "refactoring": "Refactoring is risky without proper tooling. This feature helps you refactor with confidence.",
            "testing": "Testing is critical for code quality. This feature improves your testing workflow.",
            "typing": "Strong typing catches errors early. This feature enhances type safety.",
        }

        for category in categories:
            if category in context_templates:
                return context_templates[category]

        return f"This feature is relevant to your {', '.join(tech_stack)} stack."

    def _find_code_example(self, feature: Dict) -> Optional[Dict]:
        """Find a relevant code example from the repo."""
        # For now, return a placeholder
        # In production, this would search the repo for relevant code
        return {
            "file": "Example file from your repo",
            "language": self.tech_stack[0] if self.tech_stack else "python",
            "snippet": "# Example code would be extracted here\n# based on feature relevance",
        }

    def _generate_improvement_statement(self, feature: Dict) -> str:
        """Generate a statement about how this improves the user's workflow."""
        categories = feature.get("categories", [])
        score = feature.get("workflow_score", 0)

        if score >= 75:
            impact_level = "significantly improve"
        elif score >= 50:
            impact_level = "improve"
        else:
            impact_level = "potentially improve"

        if categories:
            area = categories[0].replace("_", " ")
            return (
                f"This feature can {impact_level} your {area} workflow "
                f"in your {', '.join(self.tech_stack)} codebase."
            )
        else:
            return f"This feature can {impact_level} your development workflow."

    def _estimate_impact(self, feature: Dict) -> Dict:
        """Estimate the practical impact of this feature."""
        categories = feature.get("categories", [])
        score = feature.get("workflow_score", 0)

        # Map to estimated time/impact
        impact_map = {
            "performance": "Could reduce build/test times by 5-20%",
            "debugging": "Could speed up debugging by 10-30%",
            "refactoring": "Enables safer large-scale refactoring",
            "testing": "Could improve test coverage by 5-15%",
            "typing": "Prevents 5-15% of common runtime errors",
        }

        estimates = []
        for category in categories:
            if category in impact_map:
                estimates.append(impact_map[category])

        return {
            "confidence": "high" if score >= 60 else "medium",
            "estimated_benefit": estimates[0] if estimates else "Improves development workflow",
            "effort_to_adopt": "Low" if score >= 70 else "Medium",
        }

    def _generate_personalized_impact(self, feature: Dict) -> Dict:
        """
        Generate personalized impact statement based on code analysis and chronicle data.

        This is the "Why This Matters To YOU" section with concrete examples.
        """
        if not self.pattern_matcher and not self.code_analysis:
            return self._get_default_personalization(feature)

        title = feature.get("title", "")

        # Use pattern matcher if available
        if self.pattern_matcher:
            try:
                match = self.pattern_matcher.match_feature_to_patterns(feature)
                return {
                    "headline": f"Why {title} Matters To YOU",
                    "affected_files": match.get("affected_files", []),
                    "time_saved_per_week": match.get("estimated_time_saved_per_week", 0),
                    "reasoning": match.get("reasoning", ""),
                    "confidence": match.get("confidence", 0.5),
                    "next_steps": self._generate_next_steps(
                        title, match.get("affected_files", [])
                    ),
                }
            except Exception:
                pass

        # Fallback: use code analysis for basic personalization
        if self.code_analysis:
            patterns = self.code_analysis.get("patterns", {})
            file_patterns = self.code_analysis.get("file_patterns", {})

            # Find relevant files based on feature
            relevant_files = self._find_relevant_files_for_feature(title, patterns)

            return {
                "headline": f"Why {title} Matters To YOU",
                "affected_files": relevant_files[:3],
                "time_saved_per_week": self._estimate_time_from_patterns(
                    title, patterns
                ),
                "reasoning": f"We found code patterns in {len(relevant_files)} files that would benefit from {title}.",
                "confidence": 0.5 + (len(relevant_files) * 0.1),
                "next_steps": self._generate_next_steps(title, relevant_files[:3]),
            }

        return self._get_default_personalization(feature)

    def _get_default_personalization(self, feature: Dict) -> Dict:
        """Default personalization when no analysis available."""
        title = feature.get("title", "")
        categories = feature.get("categories", [])

        return {
            "headline": f"Why {title} Matters To YOU",
            "affected_files": [],
            "time_saved_per_week": 1.0,
            "reasoning": f"This feature addresses {categories[0] if categories else 'development workflow'} challenges.",
            "confidence": 0.5,
            "next_steps": ["Enable this feature in your Copilot settings", "Try it on your next task"],
        }

    def _find_relevant_files_for_feature(
        self, feature_title: str, patterns: Dict
    ) -> List[str]:
        """Find files relevant to this feature based on code patterns."""
        feature_patterns = self._map_feature_to_patterns(feature_title)
        relevant_files = []

        for pattern in feature_patterns:
            for issue in patterns.get(pattern, []):
                file_path = issue.get("file")
                if file_path and file_path not in relevant_files:
                    relevant_files.append(file_path)

        return relevant_files[:3]

    def _map_feature_to_patterns(self, feature_title: str) -> List[str]:
        """Map feature to code pattern types."""
        feature_lower = feature_title.lower()

        mapping = {
            "critic": ["async_issues", "error_handling", "debugging"],
            "debug": ["debugging", "error_handling"],
            "test": ["testing"],
            "refactor": ["code_organization"],
            "performance": ["performance", "async_issues"],
            "workflow": ["code_organization", "async_issues"],
            "agentic": ["code_organization", "async_issues"],
        }

        for key, patterns in mapping.items():
            if key in feature_lower:
                return patterns

        return []

    def _estimate_time_from_patterns(self, feature_title: str, patterns: Dict) -> float:
        """Estimate time savings from code patterns found."""
        relevant_patterns = self._map_feature_to_patterns(feature_title)

        total_issues = 0
        for pattern in relevant_patterns:
            total_issues += len(patterns.get(pattern, []))

        # Rough estimate: 30 mins per 5 issues × 0.2 (20% savings)
        if total_issues > 0:
            return round((total_issues / 5) * 0.5 * 0.2, 1)

        return 1.0

    def _generate_next_steps(self, feature_title: str, affected_files: List[str]) -> List[str]:
        """Generate concrete next steps for using this feature."""
        steps = []

        if affected_files:
            steps.append(f"Start with {affected_files[0]}")
        else:
            steps.append(f"Enable {feature_title} in your Copilot settings")

        # Add feature-specific next steps
        feature_lower = feature_title.lower()
        if "critic" in feature_lower or "bug" in feature_lower:
            steps.append("Run Critic Agent on your next pull request")
        elif "test" in feature_lower:
            steps.append("Generate test cases for untested functions")
        elif "refactor" in feature_lower:
            steps.append("Try safe refactoring on complex functions")
        elif "debug" in feature_lower:
            steps.append("Use enhanced debugging on your next bug investigation")
        elif "performance" in feature_lower:
            steps.append("Profile your code to find bottlenecks")

        return steps

    def to_json(self, use_cases: List[Dict]) -> str:
        """Convert use cases to JSON."""
        return json.dumps(use_cases, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            features = json.load(f)

        # Mock repo context
        repo_context = {
            "tech_stack": ["python"],
            "dependencies": {},
            "path": ".",
        }

        generator = UseCaseGenerator(".", repo_context)
        use_cases = generator.generate_use_cases(features, top_n=3)
        print(generator.to_json(use_cases))
