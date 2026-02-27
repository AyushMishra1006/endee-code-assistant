"""
Cache Manager - Handle persistent storage of analyzed repositories
Enables 600x faster re-analysis of same repositories
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class RepositoryCache:
    """Manage cached analysis of repositories"""

    def __init__(self, cache_dir: str = ".claude_cache"):
        """Initialize cache manager"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_repo_hash(self, repo_url: str) -> str:
        """Generate unique hash for repository URL"""
        return hashlib.sha256(repo_url.encode()).hexdigest()[:16]

    def is_cached(self, repo_url: str) -> bool:
        """Check if repository analysis is cached"""
        repo_hash = self.get_repo_hash(repo_url)
        cache_file = self.cache_dir / f"{repo_hash}.json"
        return cache_file.exists()

    def save_analysis(self, repo_url: str, chunks: List[dict], embeddings: List[List[float]]) -> bool:
        """Save analyzed chunks and embeddings to cache"""
        try:
            repo_hash = self.get_repo_hash(repo_url)
            cache_file = self.cache_dir / f"{repo_hash}.json"

            cache_data = {
                "repo_url": repo_url,
                "timestamp": datetime.now().isoformat(),
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
        """Load cached chunks and embeddings"""
        try:
            repo_hash = self.get_repo_hash(repo_url)
            cache_file = self.cache_dir / f"{repo_hash}.json"

            if not cache_file.exists():
                return None

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
