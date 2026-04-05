"""
Generate grounded use cases: Create actionable workflow improvements from repo code.
"""

import json
from typing import List, Dict, Optional
import os
from pathlib import Path


class UseCaseGenerator:
    """Generate workflow-focused use cases grounded in actual repo code."""

    def __init__(self, repo_path: str, repo_context: Dict):
        """Initialize generator with repo path and context."""
        self.repo_path = Path(repo_path).resolve()
        self.repo_context = repo_context
        self.tech_stack = repo_context.get("tech_stack", [])

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
