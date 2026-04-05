"""
Relevance scorer: rank changelog features by workflow impact using Copilot CLI.
Scores by: tech stack overlap + workflow improvement potential.
"""

import json
import subprocess
import re
from typing import List, Dict, Tuple


class RelevanceScorer:
    """Score changelog features for workflow impact and relevance."""

    def __init__(self, repo_context: Dict, user_context: Dict):
        """Initialize scorer with repo and user context."""
        self.repo_context = repo_context
        self.user_context = user_context
        self.tech_stack = repo_context.get("tech_stack", [])
        self.dependencies = repo_context.get("dependencies", {})

    def score_features(self, features: List[Dict]) -> List[Dict]:
        """
        Score each feature for workflow impact.
        Returns features sorted by score (highest first).
        """
        scored = []

        for feature in features:
            score = self._score_single_feature(feature)
            feature_with_score = feature.copy()
            feature_with_score["workflow_score"] = score["total"]
            feature_with_score["score_breakdown"] = score["breakdown"]
            scored.append(feature_with_score)

        # Sort by score descending
        scored.sort(key=lambda x: x["workflow_score"], reverse=True)
        return scored

    def _score_single_feature(self, feature: Dict) -> Dict:
        """Score a single feature across multiple dimensions."""
        breakdown = {
            "tech_stack_match": self._score_tech_stack_match(feature),
            "workflow_impact": self._score_workflow_impact(feature),
            "user_context_match": self._score_user_context_match(feature),
        }

        # Weighted sum: tech (30%) + workflow (50%) + user context (20%)
        base_score = (
            breakdown["tech_stack_match"] * 0.30
            + breakdown["workflow_impact"] * 0.50
            + breakdown["user_context_match"] * 0.20
        )

        # Apply source authority weighting (API: 100%, Markdown: 80%, Docs: 60%)
        authority = feature.get("authority", 100)  # Default to API authority
        authority_multiplier = authority / 100.0
        total = base_score * authority_multiplier
        breakdown["source_authority"] = authority

        return {"total": total, "breakdown": breakdown}

    def _score_tech_stack_match(self, feature: Dict) -> float:
        """Score 0-100: Does this feature match the repo's tech stack?"""
        title = (feature.get("title") or "").lower()
        description = (feature.get("description") or "").lower()
        keywords_found = feature.get("impact_keywords", [])

        # Check for explicit mentions of tech stack
        text = title + " " + description
        tech_mentions = 0

        for tech in self.tech_stack:
            if tech.lower() in text:
                tech_mentions += 1

        # Check for language-specific keywords
        if "python" in self.tech_stack:
            if any(
                kw in text
                for kw in [
                    "python",
                    "django",
                    "fastapi",
                    "flask",
                    "pytest",
                    "dataclass",
                ]
            ):
                tech_mentions += 1

        if any(tech in self.tech_stack for tech in ["node", "react", "nextjs"]):
            if any(
                kw in text
                for kw in ["javascript", "typescript", "react", "node", "npm", "webpack"]
            ):
                tech_mentions += 1

        if "go" in self.tech_stack:
            if any(
                kw in text
                for kw in ["golang", "go", "concurrency", "goroutine"]
            ):
                tech_mentions += 1

        # Score: base 20 + 20 per tech match (capped at 100)
        score = 20 + (tech_mentions * 20)
        return min(score, 100)

    def _score_workflow_impact(self, feature: Dict) -> float:
        """Score 0-100: How much could this improve the user's workflow?"""
        title = (feature.get("title") or "").lower()
        description = (feature.get("description") or "").lower()
        categories = feature.get("categories", [])
        keywords_found = feature.get("impact_keywords", [])

        score = 0.0

        # Base score for having impact keywords
        if keywords_found:
            score += 30.0

        # Category-based scoring (high impact categories)
        high_impact = {"performance", "debugging", "refactoring", "testing"}
        for category in categories:
            if category in high_impact:
                score += 25.0

        # Keyword-specific bonuses
        high_value_keywords = {
            "faster": 15,
            "performance": 15,
            "debug": 20,
            "refactor": 15,
            "test": 12,
            "type": 10,
            "security": 20,
            "error": 15,
        }

        for keyword, bonus in high_value_keywords.items():
            if keyword in keywords_found:
                score += bonus

        # Check for "new" or "added" (high signal for usefulness)
        if any(word in title for word in ["new", "add", "support", "launch"]):
            score += 15

        return min(score, 100)

    def _score_user_context_match(self, feature: Dict) -> float:
        """Score 0-100: Does this match user's recent activity/interests?"""
        # If user context is limited, return neutral score
        user_tips = self.user_context.get("recent_tips", [])
        focus_areas = self.user_context.get("focus_areas", [])

        if not user_tips and not focus_areas:
            # Fallback: neutral score
            return 50.0

        title = (feature.get("title") or "").lower()
        description = (feature.get("description") or "").lower()
        text = title + " " + description

        score = 50.0  # Base neutral score

        # Bonus if categories match focus areas
        for focus in focus_areas:
            if focus.lower() in text:
                score += 15.0

        return min(score, 100)

    def to_json(self, scored_features: List[Dict]) -> str:
        """Convert scored features to JSON."""
        return json.dumps(scored_features, indent=2)


if __name__ == "__main__":
    import sys

    # Test: read features JSON and score
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            features = json.load(f)

        # Mock repo context
        repo_context = {
            "tech_stack": ["python", "node"],
            "dependencies": {"python": ["requests", "pytest"]},
        }
        user_context = {"focus_areas": [], "recent_tips": []}

        scorer = RelevanceScorer(repo_context, user_context)
        scored = scorer.score_features(features)
        print(scorer.to_json(scored))
