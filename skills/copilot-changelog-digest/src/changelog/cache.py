"""
Simple JSON-based cache for docs crawl results with timestamp-based invalidation.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class DocsCache:
    """Cache for docs crawl results with TTL-based invalidation."""

    def __init__(self, cache_file: str = ".docs_cache.json", ttl_hours: int = 24):
        """
        Initialize cache.
        
        Args:
            cache_file: Path to cache JSON file
            ttl_hours: Time-to-live for cache entries (default 24 hours)
        """
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours
        self.cache: Dict = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from disk if it exists and is valid."""
        if not os.path.exists(self.cache_file):
            return {"version": 1, "entries": {}, "metadata": {}}

        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)
                # Validate cache structure
                if "version" not in cache or "entries" not in cache:
                    return {"version": 1, "entries": {}, "metadata": {}}
                return cache
        except (json.JSONDecodeError, IOError):
            return {"version": 1, "entries": {}, "metadata": {}}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2, default=str)
        except IOError as e:
            print(f"Warning: Failed to save cache: {e}")

    def is_valid(self, key: str) -> bool:
        """Check if cache entry exists and is still valid."""
        if key not in self.cache["entries"]:
            return False

        entry = self.cache["entries"][key]
        if "timestamp" not in entry:
            return False

        cached_time = datetime.fromisoformat(entry["timestamp"])
        expired = datetime.utcnow() - cached_time > timedelta(hours=self.ttl_hours)
        return not expired

    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if it exists and is valid."""
        if not self.is_valid(key):
            return None
        return self.cache["entries"][key].get("data")

    def set(self, key: str, data: Dict, metadata: Optional[Dict] = None) -> None:
        """Store value in cache with current timestamp."""
        self.cache["entries"][key] = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {},
        }
        if metadata:
            self.cache["metadata"][key] = metadata
        self._save_cache()

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache = {"version": 1, "entries": {}, "metadata": {}}
        self._save_cache()

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of cleared entries."""
        before_count = len(self.cache["entries"])
        expired_keys = [k for k in self.cache["entries"] if not self.is_valid(k)]
        for key in expired_keys:
            del self.cache["entries"][key]
            if key in self.cache["metadata"]:
                del self.cache["metadata"][key]
        if expired_keys:
            self._save_cache()
        return len(expired_keys)

    def get_all_valid(self) -> Dict[str, Dict]:
        """Get all valid (non-expired) cache entries."""
        return {
            k: v["data"]
            for k, v in self.cache["entries"].items()
            if self.is_valid(k)
        }

    def stats(self) -> Dict:
        """Get cache statistics."""
        total_entries = len(self.cache["entries"])
        valid_entries = sum(1 for k in self.cache["entries"] if self.is_valid(k))
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "ttl_hours": self.ttl_hours,
        }
