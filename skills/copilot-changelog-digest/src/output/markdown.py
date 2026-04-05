"""
Markdown report generator: Create focused, actionable output.
"""

import json
from typing import List, Dict
from datetime import datetime


class MarkdownReportGenerator:
    """Generate a focused markdown report of top changelog items."""

    def __init__(self, repo_name: str = "repository", days: int = 7):
        """Initialize generator."""
        self.repo_name = repo_name
        self.days = days
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def generate_report(self, features_with_usecases: List[Dict]) -> str:
        """Generate markdown report from scored features with use cases."""
        lines = []

        # Header
        lines.append(f"# Copilot Changelog Update - {self.repo_name}")
        lines.append("")
        lines.append(
            f"**Most important Copilot updates in the last {self.days} days** | "
            f"Generated: {self.timestamp}"
        )
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"Found **{len(features_with_usecases)} important updates** that could improve your workflow."
        )
        lines.append(
            "Below are the most impactful changes, ranked by how much they can benefit YOUR codebase."
        )
        lines.append("")

        # NEW: Key Changes & What Matters Most To You
        lines.extend(self._generate_key_changes_section(features_with_usecases))
        lines.append("")

        # Table of contents
        lines.append("## Top Recommendations")
        lines.append("")

        for i, feature in enumerate(features_with_usecases, 1):
            title = feature.get("title", "Unknown")
            lines.append(f"{i}. {title}")

        lines.append("")

        # Detailed sections
        lines.append("## Details")
        lines.append("")

        for i, feature in enumerate(features_with_usecases, 1):
            lines.extend(self._format_feature_section(feature, i))
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("## How to Learn More")
        lines.append("")
        lines.append(
            "- Visit the [Copilot Release Notes](https://github.com/github/copilot-language-server-release/releases)"
        )
        lines.append(
            "- Check the [Copilot Documentation](https://docs.github.com/en/copilot)"
        )
        lines.append("")

        return "\n".join(lines)

    def _format_feature_section(self, feature: Dict, index: int) -> List[str]:
        """Format a single feature section."""
        lines = []

        # Feature header with score
        title = feature.get("title", "Unknown")
        score = feature.get("workflow_score", 0)
        version = feature.get("version", "N/A")

        lines.append(f"### {index}. {title}")
        lines.append("")
        lines.append(f"**Version:** {version} | **Relevance Score:** {score:.0f}/100")
        lines.append("")

        # Description
        description = feature.get("description", "")
        if description:
            lines.append(description)
            lines.append("")

        # NEW: Personalized impact section
        use_case = feature.get("use_case", {})
        personalized = use_case.get("why_this_matters_to_you", {})
        if personalized:
            lines.append("#### Why This Matters To YOU")
            lines.append("")

            headline = personalized.get("headline", "")
            if headline:
                lines.append(f"**{headline}**")
                lines.append("")

            reasoning = personalized.get("reasoning", "")
            if reasoning:
                lines.append(reasoning)
                lines.append("")

            affected_files = personalized.get("affected_files", [])
            if affected_files:
                lines.append("**Affected Files:**")
                for file_path in affected_files:
                    lines.append(f"- `{file_path}`")
                lines.append("")

            time_saved = personalized.get("time_saved_per_week", 0)
            if time_saved > 0:
                lines.append(f"**Estimated Time Savings:** ~{time_saved} hours/week")
                lines.append("")

            next_steps = personalized.get("next_steps", [])
            if next_steps:
                lines.append("**Next Steps:**")
                for step in next_steps:
                    lines.append(f"- {step}")
                lines.append("")

        # Use case section
        if use_case:
            lines.append("#### How This Helps You")
            lines.append("")

            headline = use_case.get("headline", "")
            if headline:
                lines.append(f"**{headline}**")
                lines.append("")

            improvement = use_case.get("workflow_improvement", "")
            if improvement:
                lines.append(f"➤ {improvement}")
                lines.append("")

            context = use_case.get("context", "")
            if context:
                lines.append(context)
                lines.append("")

            # Impact estimate
            impact = use_case.get("estimated_impact", {})
            if impact:
                lines.append("#### Estimated Impact")
                lines.append("")

                benefit = impact.get("estimated_benefit", "")
                if benefit:
                    lines.append(f"- **Benefit:** {benefit}")

                confidence = impact.get("confidence", "")
                if confidence:
                    lines.append(f"- **Confidence:** {confidence.capitalize()}")

                effort = impact.get("effort_to_adopt", "")
                if effort:
                    lines.append(f"- **Effort to Adopt:** {effort}")

                lines.append("")

        # Categories and keywords
        categories = feature.get("categories", [])
        if categories and categories != ["general"]:
            lines.append(f"**Categories:** {', '.join(categories)}")
            lines.append("")

        # Link to release
        url = feature.get("url", "")
        if url:
            lines.append(f"[View Full Release Notes]({url})")
            lines.append("")

        return lines

    def _generate_key_changes_section(self, features: List[Dict]) -> List[str]:
        """Generate the 'Key Changes & What Matters Most To You' section."""
        lines = []
        lines.append("## Key Changes & What Matters Most To You")
        lines.append("")

        if not features:
            lines.append("No significant changes for your repository detected.")
            return lines

        lines.append(
            "The following changes have the highest impact on YOUR specific codebase."
        )
        lines.append("They're ranked by relevance to your code patterns and workflow.")
        lines.append("")

        for i, feature in enumerate(features[:5], 1):  # Top 5 only
            title = feature.get("title", "Unknown")
            use_case = feature.get("use_case", {})
            personalized = use_case.get("why_this_matters_to_you", {})

            # Create a concise entry
            lines.append(f"#### {i}. {title}")
            lines.append("")

            # Reasoning
            reasoning = personalized.get("reasoning", "")
            if reasoning:
                lines.append(f"🎯 {reasoning}")
                lines.append("")

            # Time savings
            time_saved = personalized.get("time_saved_per_week", 0)
            if time_saved > 0:
                hours_per_month = round(time_saved * 4.3, 1)
                lines.append(
                    f"⏱️ **Time Savings:** ~{time_saved}h/week (~{hours_per_month}h/month)"
                )
                lines.append("")

            # Quick win next step
            next_steps = personalized.get("next_steps", [])
            if next_steps:
                lines.append(f"✨ **Next Step:** {next_steps[0]}")
                lines.append("")

        return lines

    def to_string(self, report: str) -> str:
        """Return report as string (already is)."""
        return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            features = json.load(f)

        generator = MarkdownReportGenerator("MyProject", days=7)
        report = generator.generate_report(features)
        print(report)
