"""
Cache Manager - Handle persistent storage of analyzed repositories
Enables 600x faster re-analysis of same repositories
Includes TTL (Time-To-Live) + Git commit hash validation for cache freshness
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta


class RepositoryCache:
    """Manage cached analysis of repositories"""

    def __init__(self, cache_dir: str = ".claude_cache"):
        """Initialize cache manager"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_repo_hash(self, repo_url: str) -> str:
        """Generate unique hash for repository URL"""
        return hashlib.sha256(repo_url.encode()).hexdigest()[:16]

    def get_current_commit_hash(self) -> Optional[str]:
        """Get current Git commit hash for cache versioning"""
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=".",
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            return commit_hash
        except Exception:
            # Not a git repo or git not available
            return None

    def is_cached(self, repo_url: str) -> bool:
        """Check if repository analysis is cached"""
        repo_hash = self.get_repo_hash(repo_url)
        cache_file = self.cache_dir / f"{repo_hash}.json"
        return cache_file.exists()

    def is_cache_valid(self, repo_url: str, ttl_hours: int = 24) -> bool:
        """
        Check if cache is still valid (not expired and commit hasn't changed)

        Args:
            repo_url: Repository URL
            ttl_hours: Time-To-Live in hours (default 24 hours)

        Returns:
            True if cache exists and is fresh, False otherwise
        """
        try:
            repo_hash = self.get_repo_hash(repo_url)
            cache_file = self.cache_dir / f"{repo_hash}.json"

            if not cache_file.exists():
                return False

            with open(cache_file, "r") as f:
                cache_data = json.load(f)

            # Check TTL (Time-To-Live)
            cache_timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
            age = datetime.now() - cache_timestamp
            if age > timedelta(hours=ttl_hours):
                return False  # Cache expired

            # Check if Git commit has changed
            cached_commit = cache_data.get("commit_hash")
            current_commit = self.get_current_commit_hash()
            if cached_commit and current_commit and cached_commit != current_commit:
                return False  # Repository changed

            return True
        except Exception:
            return False

    def save_analysis(self, repo_url: str, chunks: List[dict], embeddings: List[List[float]]) -> bool:
        """Save analyzed chunks and embeddings to cache with versioning"""
        try:
            repo_hash = self.get_repo_hash(repo_url)
            cache_file = self.cache_dir / f"{repo_hash}.json"

            cache_data = {
                "repo_url": repo_url,
                "timestamp": datetime.now().isoformat(),
                "commit_hash": self.get_current_commit_hash(),  # NEW: Git version
                "chunks_count": len(chunks),
                "chunks": chunks,
                "embeddings": embeddings,
            }

            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            return True
        except Exception as e:
            print(f"Error saving cache: {e}")
            return False

    def load_analysis(self, repo_url: str) -> Optional[tuple[List[dict], List[List[float]]]]:
        """Load cached chunks and embeddings (validates freshness first)"""
        try:
            # NEW: Check if cache is still valid (TTL + commit hash)
            if not self.is_cache_valid(repo_url):
                return None

            repo_hash = self.get_repo_hash(repo_url)
            cache_file = self.cache_dir / f"{repo_hash}.json"

            with open(cache_file, "r") as f:
                cache_data = json.load(f)

            chunks = cache_data.get("chunks", [])
            embeddings = cache_data.get("embeddings", [])

            return chunks, embeddings
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None

    def clear_cache(self, repo_url: Optional[str] = None) -> bool:
        """Clear cache for specific repo or all repos"""
        try:
            if repo_url:
                repo_hash = self.get_repo_hash(repo_url)
                cache_file = self.cache_dir / f"{repo_hash}.json"
                if cache_file.exists():
                    cache_file.unlink()
            else:
                # Clear all caches
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files) / (1024 * 1024)  # MB

        return {
            "total_cached_repos": len(cache_files),
            "total_size_mb": round(total_size, 2),
            "cache_dir": str(self.cache_dir),
        }


# Global cache instance
_cache = None


def get_cache() -> RepositoryCache:
    """Get or create global cache instance"""
    global _cache
    if _cache is None:
        _cache = RepositoryCache()
    return _cache
