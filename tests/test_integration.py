"""
Integration tests for Copilot Changelog Skill.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fleet.orchestrator import FleetOrchestrator
from src.changelog.parser import ChangelogParser
from src.ranking.scorer import RelevanceScorer


def test_fleet_orchestration():
    """Test Phase 1: Fleet orchestration and data retrieval."""
    print("Testing Phase 1: Fleet Orchestration...")
    
    orchestrator = FleetOrchestrator(".", days=7)
    results = orchestrator.run_parallel_tasks()
    
    assert results is not None, "Fleet orchestrator returned None"
    assert "changelog" in results, "Missing changelog data"
    assert "repo_context" in results, "Missing repo context"
    assert "user_context" in results, "Missing user context"
    assert results["all_tasks_successful"] is True, "One or more tasks failed"
    
    print("✓ Phase 1 passed")
    return results


def test_changelog_parsing(phase1_results):
    """Test Phase 2a: Changelog parsing."""
    print("Testing Phase 2a: Changelog Parsing...")
    
    changelog = phase1_results.get("changelog", [])
    parser = ChangelogParser()
    features = parser.parse_releases(changelog)
    
    assert len(features) > 0, "No features parsed"
    
    # Validate feature structure
    for feature in features:
        assert "version" in feature, "Missing version"
        assert "title" in feature, "Missing title"
        assert "categories" in feature, "Missing categories"
    
    print(f"✓ Phase 2a passed ({len(features)} features parsed)")
    return features


def test_relevance_scoring(phase1_results, features):
    """Test Phase 2b: Relevance scoring."""
    print("Testing Phase 2b: Relevance Scoring...")
    
    repo_context = phase1_results.get("repo_context", {})
    user_context = phase1_results.get("user_context", {})
    
    scorer = RelevanceScorer(repo_context, user_context)
    scored_features = scorer.score_features(features)
    
    assert len(scored_features) > 0, "No features scored"
    
    # Validate scoring
    for feature in scored_features:
        assert "workflow_score" in feature, "Missing workflow_score"
        assert 0 <= feature["workflow_score"] <= 100, "Score out of range"
        assert "score_breakdown" in feature, "Missing score breakdown"
    
    # Verify sorting (highest scores first)
    scores = [f["workflow_score"] for f in scored_features]
    assert scores == sorted(scores, reverse=True), "Features not sorted by score"
    
    print(f"✓ Phase 2b passed (top score: {scores[0]:.0f})")
    return scored_features


def main():
    """Run all integration tests."""
    print("=" * 80)
    print("Copilot Changelog Skill - Integration Tests")
    print("=" * 80)
    print()
    
    try:
        phase1_results = test_fleet_orchestration()
        print()
        
        features = test_changelog_parsing(phase1_results)
        print()
        
        scored_features = test_relevance_scoring(phase1_results, features)
        print()
        
        print("=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
        
        return 0
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
