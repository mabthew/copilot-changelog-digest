"""
Main Python backend orchestrator for Copilot Changelog Skill.
Manages Phase 1-5 execution.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fleet.orchestrator import FleetOrchestrator
from src.changelog.parser import ChangelogParser
from src.ranking.scorer import RelevanceScorer
from src.generation.use_cases import UseCaseGenerator
from src.output.markdown import MarkdownReportGenerator


def main():
    """Main entry point for Python backend."""
    parser = argparse.ArgumentParser(
        description="Copilot Changelog Skill - Analyze and rank Copilot changelog by workflow impact"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Time window in days (default: 7)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Repository path (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["markdown", "interactive", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Phase 1: Parallel data retrieval via /fleet
    print(f"Phase 1: Fetching data for last {args.days} days...")
    orchestrator = FleetOrchestrator(args.repo, args.days)
    phase1_results = orchestrator.run_parallel_tasks()

    # Phase 2: Ranking & Relevance Scoring
    print("Phase 2: Ranking & scoring...")
    phase2_results = _run_phase2(phase1_results)

    # Phase 3: Use Case Generation
    print("Phase 3: Generating use cases...")
    phase3_results = _run_phase3(phase1_results, phase2_results)

    # Phase 4: Output Generation
    print("Phase 4: Generating report...")
    phase4_results = _run_phase4(phase3_results, args)

    # Output based on requested format
    if args.output == "markdown":
        # For markdown output, just print the report
        print("\n" + "=" * 80)
        print(phase4_results["report"])
    else:
        # For JSON, return complete pipeline
        output = {
            "phase": 4,
            "status": "complete",
            "phases": {
                "phase1": {"data": phase1_results},
                "phase2": {"data": phase2_results},
                "phase3": {"data": phase3_results},
                "phase4": {"report": phase4_results["report"]},
            },
        }
        print(json.dumps(output, indent=2))


def _run_phase2(phase1_results: Dict) -> Dict:
    """Execute Phase 2: Parse and score changelog."""
    changelog_data = phase1_results.get("changelog", [])
    repo_context = phase1_results.get("repo_context", {})
    user_context = phase1_results.get("user_context", {})

    # Parse changelog
    changelog_parser = ChangelogParser()
    parsed_features = changelog_parser.parse_releases(changelog_data)

    # Score features
    scorer = RelevanceScorer(repo_context, user_context)
    scored_features = scorer.score_features(parsed_features)

    return {
        "parsed_features_count": len(parsed_features),
        "scored_features": scored_features,
    }


def _run_phase3(phase1_results: Dict, phase2_results: Dict) -> Dict:
    """Execute Phase 3: Generate use cases."""
    repo_context = phase1_results.get("repo_context", {})
    repo_path = phase1_results.get("repo_path", ".")
    scored_features = phase2_results.get("scored_features", [])

    # Generate use cases for top 5 features
    generator = UseCaseGenerator(repo_path, repo_context)
    features_with_usecases = generator.generate_use_cases(scored_features, top_n=5)

    return {
        "features_with_usecases_count": len(features_with_usecases),
        "features": features_with_usecases,
    }


def _run_phase4(phase3_results: Dict, args) -> Dict:
    """Execute Phase 4: Generate markdown report."""
    features_with_usecases = phase3_results.get("features", [])

    # Extract repo name from path
    repo_path = Path(args.repo).resolve()
    repo_name = repo_path.name if repo_path.name else "repository"

    # Generate markdown report
    report_generator = MarkdownReportGenerator(repo_name, days=args.days)
    markdown_report = report_generator.generate_report(features_with_usecases)

    return {"report": markdown_report}


if __name__ == "__main__":
    main()
