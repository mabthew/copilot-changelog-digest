"""Tests for Phase 4 Chronicle Integration and Code Analysis."""

import pytest
import json
import sys
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chronicle.client import ChronicleClient, ChronicleCache
from src.insights.code_analyzer import CodeAnalyzer
from src.insights.pattern_matcher import PatternMatcher
from src.generation.use_cases import UseCaseGenerator


class TestChronicleCache:
    """Test Chronicle cache functionality."""

    def test_cache_get_set(self):
        """Test basic cache get/set operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChronicleCache(cache_dir=Path(tmpdir), ttl_minutes=30)

            # Set value
            test_data = {"key": "value"}
            cache.set("test_key", test_data)

            # Get value
            result = cache.get("test_key")
            assert result == test_data

    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChronicleCache(cache_dir=Path(tmpdir), ttl_minutes=0)

            test_data = {"key": "value"}
            cache.set("test_key", test_data)

            # Should be expired immediately with 0 TTL
            result = cache.get("test_key")
            assert result is None

    def test_cache_clear(self):
        """Test cache clear operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChronicleCache(cache_dir=Path(tmpdir), ttl_minutes=30)

            cache.set("key1", {"data": 1})
            cache.set("key2", {"data": 2})

            cache.clear()

            assert cache.get("key1") is None
            assert cache.get("key2") is None


class TestChronicleClient:
    """Test Chronicle API client."""

    def test_chronicle_client_initialization(self):
        """Test client initialization."""
        client = ChronicleClient()
        assert client.cache is not None
        assert isinstance(client.available, bool)

    def test_fallback_patterns_from_git(self):
        """Test fallback pattern extraction from git."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Initialize git repo
            import subprocess
            subprocess.run(
                ["git", "init"],
                cwd=str(repo_path),
                capture_output=True,
            )

            # Create and commit a test file
            test_file = repo_path / "test.py"
            test_file.write_text("print('hello')")
            subprocess.run(
                ["git", "add", "test.py"],
                cwd=str(repo_path),
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=str(repo_path),
                capture_output=True,
                env={**dict(subprocess.os.environ), "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com"},
            )

            client = ChronicleClient()
            patterns = client.fetch_user_patterns(str(repo_path))

            assert patterns["success"] is True
            assert "recent_files" in patterns
            assert "frequent_files" in patterns
            assert "workflow_patterns" in patterns

    def test_get_personalization_context(self):
        """Test personalization context extraction."""
        client = ChronicleClient()
        context = client.get_personalization_context(".")

        assert "recent_files" in context
        assert "frequent_files" in context
        assert "workflow_patterns" in context
        assert "error_patterns" in context
        assert "focus_areas" in context
        assert "available" in context


class TestCodeAnalyzer:
    """Test code pattern analyzer."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = CodeAnalyzer(".")
        assert analyzer.repo_path.is_absolute()

    def test_analyze_repository(self):
        """Test repository analysis."""
        analyzer = CodeAnalyzer(".")
        analysis = analyzer.analyze_repository()

        assert "patterns" in analysis
        assert "file_patterns" in analysis
        assert "summary" in analysis

        patterns = analysis["patterns"]
        assert "async_issues" in patterns
        assert "error_handling" in patterns
        assert "testing" in patterns
        assert "code_organization" in patterns
        assert "performance" in patterns
        assert "debugging" in patterns

    def test_detect_async_issues(self):
        """Test async pattern detection."""
        analyzer = CodeAnalyzer(".")

        # Test Promise.all without error handling
        code = "Promise.all([p1, p2, p3]);"
        issues = analyzer._detect_async_issues(code, "test.js")
        assert len(issues) > 0

    def test_detect_error_handling(self):
        """Test error handling detection."""
        analyzer = CodeAnalyzer(".")

        # Test empty catch block
        code = "try { risky(); } catch (e) { }"
        issues = analyzer._detect_error_handling(code, "test.js")
        assert len(issues) > 0

    def test_get_files_for_pattern(self):
        """Test getting files with specific pattern."""
        analyzer = CodeAnalyzer(".")
        files = analyzer.get_files_for_pattern("testing", limit=3)

        assert isinstance(files, list)
        assert len(files) <= 3


class TestPatternMatcher:
    """Test feature-to-pattern matching."""

    def test_matcher_initialization(self):
        """Test matcher initialization."""
        code_analysis = {
            "patterns": {"async_issues": [], "error_handling": []},
            "file_patterns": {},
        }
        chronicle_context = {"workflow_patterns": {}, "error_patterns": []}
        repo_context = {}

        matcher = PatternMatcher(code_analysis, chronicle_context, repo_context)
        assert matcher is not None

    def test_match_feature_to_patterns(self):
        """Test feature matching."""
        code_analysis = {
            "patterns": {
                "async_issues": [
                    {"file": "test.js", "line": 1, "pattern": "Promise.all"},
                ],
                "error_handling": [],
            },
            "file_patterns": {"test.js": ["async_issues"]},
        }
        chronicle_context = {"workflow_patterns": {"uses_debugging": True}}
        repo_context = {}

        matcher = PatternMatcher(code_analysis, chronicle_context, repo_context)

        feature = {
            "title": "Critic Agent",
            "description": "Detects bugs in async code",
        }

        match = matcher.match_feature_to_patterns(feature)

        assert "feature" in match
        assert match["feature"] == "Critic Agent"
        assert "matched_patterns" in match
        assert "estimated_time_saved_per_week" in match
        assert "confidence" in match
        assert match["confidence"] >= 0.0
        assert match["confidence"] <= 1.0


class TestUseCaseGenerator:
    """Test enhanced use case generation with personalization."""

    def test_generator_with_personalization(self):
        """Test use case generation with code analysis and chronicle."""
        code_analysis = {
            "patterns": {
                "async_issues": [
                    {"file": "src/api.js", "line": 10, "pattern": "Promise.all"},
                ],
                "error_handling": [],
                "testing": [],
                "code_organization": [],
                "performance": [],
                "debugging": [],
            },
            "file_patterns": {"src/api.js": ["async_issues"]},
        }

        chronicle_context = {
            "recent_files": ["src/api.js", "src/main.js"],
            "workflow_patterns": {"uses_debugging": True},
            "error_patterns": ["timeout", "race condition"],
            "focus_areas": ["api"],
        }

        generator = UseCaseGenerator(
            ".",
            {"tech_stack": ["javascript"]},
            code_analysis=code_analysis,
            chronicle_context=chronicle_context,
        )

        feature = {
            "title": "Critic Agent",
            "description": "Catches bugs in async code",
            "categories": ["debugging"],
            "workflow_score": 85,
        }

        # Generate single use case
        use_case = generator._generate_single_use_case(feature)

        assert "headline" in use_case
        assert "context" in use_case
        assert "why_this_matters_to_you" in use_case
        assert "estimated_impact" in use_case

        # Check personalization
        personalized = use_case.get("why_this_matters_to_you", {})
        assert personalized is not None

    def test_personalized_impact_with_pattern_matcher(self):
        """Test personalized impact generation with pattern matcher."""
        code_analysis = {
            "patterns": {
                "async_issues": [
                    {"file": "src/api.js", "line": 10, "pattern": "Promise.all"},
                ],
                "error_handling": [],
                "testing": [],
                "code_organization": [],
                "performance": [],
                "debugging": [],
            },
            "file_patterns": {"src/api.js": ["async_issues"]},
        }

        chronicle_context = {
            "recent_files": ["src/api.js"],
            "workflow_patterns": {},
            "error_patterns": [],
            "focus_areas": [],
        }

        matcher = PatternMatcher(code_analysis, chronicle_context, {})

        generator = UseCaseGenerator(
            ".",
            {"tech_stack": ["javascript"]},
            code_analysis=code_analysis,
            chronicle_context=chronicle_context,
            pattern_matcher=matcher,
        )

        feature = {
            "title": "Critic Agent",
            "description": "Async debugging",
            "categories": ["debugging"],
        }

        impact = generator._generate_personalized_impact(feature)

        assert "headline" in impact
        assert "Why" in impact["headline"]
        assert "affected_files" in impact
        assert "time_saved_per_week" in impact


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
