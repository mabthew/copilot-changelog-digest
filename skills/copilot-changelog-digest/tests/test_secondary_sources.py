"""
Tests for Phase 2: Secondary data sources (markdown parsing and docs crawling).
Tests cache system, markdown parser, docs crawler, and source integration.
"""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.changelog.cache import DocsCache
from src.changelog.markdown_parser import MarkdownChangelogParser
from src.changelog.docs_crawler import DocsCrawler
from src.changelog.fetcher import ChangelogFetcher


def test_cache_system():
    """Test Phase 2: Cache system with TTL invalidation."""
    print("Testing cache system...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        cache_file = f.name

    try:
        cache = DocsCache(cache_file=cache_file, ttl_hours=1)

        # Test basic set/get
        test_data = {"key": "value", "number": 42}
        cache.set("test_key", test_data)
        retrieved = cache.get("test_key")
        assert retrieved == test_data, "Cache retrieval failed"

        # Test invalid (non-existent) key
        assert cache.get("non_existent") is None, "Non-existent key should return None"

        # Test stats
        stats = cache.stats()
        assert stats["valid_entries"] == 1, "Stats should show 1 valid entry"
        assert stats["ttl_hours"] == 1, "TTL should be 1 hour"

        # Test metadata storage
        metadata = {"source": "test", "timestamp": datetime.utcnow().isoformat()}
        cache.set("meta_key", test_data, metadata)
        assert cache.get("meta_key") == test_data, "Metadata storage failed"

        # Test clear
        cache.clear()
        assert cache.get("test_key") is None, "Clear failed"
        stats_after_clear = cache.stats()
        assert stats_after_clear["total_entries"] == 0, "Clear should remove all entries"

        print("✓ Cache system tests passed")
        return True

    finally:
        Path(cache_file).unlink(missing_ok=True)


def test_markdown_parser():
    """Test Phase 2: Markdown changelog parser."""
    print("Testing markdown parser...")

    parser = MarkdownChangelogParser()

    # Test fetch (real data)
    print("  - Fetching changelog.md from github/copilot-cli...")
    try:
        raw_md = parser.fetch_changelog_markdown()
        assert raw_md is not None, "Failed to fetch changelog.md"
        assert len(raw_md) > 0, "Changelog.md is empty"
        print(f"    ✓ Fetched {len(raw_md)} characters")
    except Exception as e:
        print(f"    ✗ Failed to fetch: {e}")
        return False

    # Test parsing
    print("  - Parsing markdown structure...")
    try:
        entries = parser.parse_changelog_markdown(raw_md)
        assert len(entries) > 0, "No entries parsed"
        print(f"    ✓ Parsed {len(entries)} changelog entries")
    except Exception as e:
        print(f"    ✗ Failed to parse: {e}")
        return False

    # Validate entry structure
    print("  - Validating entry structure...")
    for entry in entries[:3]:  # Check first 3
        assert hasattr(entry, "version"), "Missing version"
        assert hasattr(entry, "date"), "Missing date"
        assert hasattr(entry, "section"), "Missing section"
        assert hasattr(entry, "features"), "Missing features"
        assert isinstance(entry.features, list), "Features should be list"

    # Test JSON conversion
    print("  - Testing JSON serialization...")
    dict_list = parser.to_dict_list(entries)
    assert len(dict_list) > 0, "JSON conversion failed"
    json_str = json.dumps(dict_list)  # Should not raise
    assert len(json_str) > 0, "JSON string is empty"

    print("✓ Markdown parser tests passed")
    return True


def test_docs_crawler():
    """Test Phase 2: Docs crawler initialization and basic functionality."""
    print("Testing docs crawler...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        cache_file = f.name

    try:
        cache = DocsCache(cache_file=cache_file, ttl_hours=24)

        # Test initialization
        print("  - Initializing crawler...")
        crawler = DocsCrawler(days=7, cache=cache)
        assert crawler.days == 7, "Days not set correctly"
        assert crawler.DOCS_BASE == "https://docs.github.com/en/copilot", "Base URL wrong"
        assert crawler.REQUEST_DELAY == 1.0, "Request delay wrong"
        print("    ✓ Crawler initialized")

        # Test cache integration
        print("  - Testing cache integration...")
        test_cache_data = [
            {"title": "Intro", "url": "https://example.com/intro", "path": "/en/copilot"}
        ]
        cache.set("copilot_docs_index", test_cache_data)
        cached = crawler.get_cached_docs()
        assert cached == test_cache_data, "Cache retrieval failed"
        print("    ✓ Cache integration works")

        print("✓ Docs crawler tests passed")
        return True

    finally:
        Path(cache_file).unlink(missing_ok=True)


def test_source_integration():
    """Test Phase 2: Integration of all 3 sources in ChangelogFetcher."""
    print("Testing source integration...")

    fetcher = ChangelogFetcher(days=7)

    # Test individual sources
    print("  - Fetching from API...")
    try:
        api_releases = fetcher.fetch_releases()
        assert isinstance(api_releases, list), "API releases should be list"
        assert len(api_releases) > 0, "No API releases fetched"
        print(f"    ✓ API: {len(api_releases)} releases")

        # Validate API source metadata
        for release in api_releases[:1]:
            assert release.get("source") == "api", "API source not marked"
            assert release.get("authority") == 100, "API authority wrong"
    except Exception as e:
        print(f"    ✗ API fetch failed: {e}")
        return False

    print("  - Fetching from markdown...")
    try:
        md_entries = fetcher.fetch_changelog_markdown()
        assert isinstance(md_entries, list), "Markdown entries should be list"
        assert len(md_entries) > 0, "No markdown entries fetched"
        print(f"    ✓ Markdown: {len(md_entries)} entries")

        # Validate markdown source metadata
        for entry in md_entries[:1]:
            assert entry.get("source") == "markdown", "Markdown source not marked"
            assert entry.get("authority") == 80, "Markdown authority wrong"
    except Exception as e:
        print(f"    ✗ Markdown fetch failed: {e}")
        return False

    print("  - Testing merged fetch (all sources)...")
    try:
        combined = fetcher.fetch_combined()
        assert isinstance(combined, list), "Combined should be list"
        assert len(combined) > 0, "No combined entries"
        print(f"    ✓ Combined: {len(combined)} entries (merged + deduplicated)")

        # Count by source
        sources = {}
        for entry in combined:
            source = entry.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        print(f"    ✓ Source breakdown:")
        for source in sorted(sources.keys()):
            print(f"      - {source}: {sources[source]}")

        # Validate that we have multiple sources
        assert len(sources) >= 2, "Should have at least 2 sources (API + markdown)"

        # Validate that docs were fetched (optional, but logged)
        if "docs.github.com" in sources:
            print(f"      ✓ Docs crawler working: {sources['docs.github.com']} entries")

    except Exception as e:
        print(f"    ✗ Combined fetch failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("✓ Source integration tests passed")
    return True


def test_authority_weighting():
    """Test Phase 2: Authority weighting in merged results."""
    print("Testing authority weighting...")

    fetcher = ChangelogFetcher(days=7)
    combined = fetcher.fetch_combined()

    # Verify authority is preserved
    authorities = {}
    for entry in combined:
        source = entry.get("source", "unknown")
        authority = entry.get("authority")
        if source not in authorities and authority is not None:
            authorities[source] = authority

    print(f"  Authority assignments:")
    expected = {"api": 100, "markdown": 80, "docs.github.com": 60}
    for source, expected_auth in expected.items():
        if source in authorities:
            actual_auth = authorities[source]
            if actual_auth == expected_auth:
                print(f"    ✓ {source}: {actual_auth}%")
            else:
                print(f"    ✗ {source}: expected {expected_auth}%, got {actual_auth}%")
                return False

    print("✓ Authority weighting tests passed")
    return True


def main():
    """Run all Phase 2 tests."""
    print("=" * 80)
    print("Copilot Changelog Skill - Phase 2 Secondary Sources Tests")
    print("=" * 80)
    print()

    tests = [
        test_cache_system,
        test_markdown_parser,
        test_docs_crawler,
        test_source_integration,
        test_authority_weighting,
    ]

    passed = 0
    failed = 0

    for test in tests:
        print()
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test {test.__name__} failed with exception: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
