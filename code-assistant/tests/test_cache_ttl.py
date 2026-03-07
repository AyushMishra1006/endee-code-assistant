"""
Test cases for Cache TTL + Git Commit Hash Validation
Tests that cache properly validates freshness and rejects stale data
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cache_manager import RepositoryCache


class TestCacheTTL:
    """Test cache TTL (Time-To-Live) validation"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temp directory"""
        return RepositoryCache(cache_dir=temp_cache_dir)

    def test_save_and_load_cache(self, cache):
        """Test basic save and load functionality"""
        repo_url = "https://github.com/test/repo"
        chunks = [{"id": 1, "text": "test"}]
        embeddings = [[0.1, 0.2, 0.3]]

        # Save
        result = cache.save_analysis(repo_url, chunks, embeddings)
        assert result is True

        # Load
        loaded_chunks, loaded_embeddings = cache.load_analysis(repo_url)
        assert loaded_chunks == chunks
        assert loaded_embeddings == embeddings

    def test_cache_stores_commit_hash(self, cache, temp_cache_dir):
        """Test that cache stores commit hash"""
        repo_url = "https://github.com/test/repo"
        chunks = [{"id": 1}]
        embeddings = [[0.1]]

        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            cache.save_analysis(repo_url, chunks, embeddings)

        # Verify commit hash in file
        repo_hash = cache.get_repo_hash(repo_url)
        cache_file = Path(temp_cache_dir) / f"{repo_hash}.json"
        with open(cache_file) as f:
            data = json.load(f)
        assert data["commit_hash"] == "abc123"

    def test_cache_expires_after_ttl(self, cache):
        """Test that cache is marked invalid after TTL expires"""
        repo_url = "https://github.com/test/repo"
        chunks = [{"id": 1}]
        embeddings = [[0.1]]

        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            cache.save_analysis(repo_url, chunks, embeddings)

        # Cache should be valid immediately
        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            assert cache.is_cache_valid(repo_url, ttl_hours=24) is True

        # Mock time to expire cache (simulate 25 hours passing)
        with patch('cache_manager.datetime') as mock_datetime:
            # Current time is old
            old_time = datetime.now() - timedelta(hours=25)
            mock_datetime.now.return_value = old_time
            mock_datetime.fromisoformat = datetime.fromisoformat

            # Save with old timestamp
            with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
                cache.save_analysis(repo_url, chunks, embeddings)

        # Cache should now be invalid (expired)
        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            assert cache.is_cache_valid(repo_url, ttl_hours=24) is False

    def test_cache_invalid_on_commit_change(self, cache):
        """Test that cache is invalid when repo commit changes"""
        repo_url = "https://github.com/test/repo"
        chunks = [{"id": 1}]
        embeddings = [[0.1]]

        # Save with commit abc123
        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            cache.save_analysis(repo_url, chunks, embeddings)

        # Cache valid with same commit
        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            assert cache.is_cache_valid(repo_url) is True

        # Cache invalid with different commit (repo changed)
        with patch.object(cache, 'get_current_commit_hash', return_value='xyz789'):
            assert cache.is_cache_valid(repo_url) is False

    def test_nonexistent_cache_returns_none(self, cache):
        """Test that loading nonexistent cache returns None"""
        result = cache.load_analysis("https://github.com/nonexistent/repo")
        assert result is None

    def test_nonexistent_cache_invalid(self, cache):
        """Test that nonexistent cache is not valid"""
        is_valid = cache.is_cache_valid("https://github.com/nonexistent/repo")
        assert is_valid is False

    def test_cache_without_git_still_works(self, cache):
        """Test cache works when git is not available"""
        repo_url = "https://github.com/test/repo"
        chunks = [{"id": 1}]
        embeddings = [[0.1]]

        # Simulate git not being available
        with patch.object(cache, 'get_current_commit_hash', return_value=None):
            result = cache.save_analysis(repo_url, chunks, embeddings)
            assert result is True

        # Should still be able to load (TTL check passes, commit check skipped)
        with patch.object(cache, 'get_current_commit_hash', return_value=None):
            loaded = cache.load_analysis(repo_url)
            assert loaded is not None

    def test_cache_stats_includes_all_files(self, cache):
        """Test cache statistics count all cached repositories"""
        # Save multiple repos
        for i in range(3):
            repo_url = f"https://github.com/test/repo{i}"
            cache.save_analysis(repo_url, [{"id": i}], [[0.1]])

        stats = cache.get_cache_stats()
        assert stats["total_cached_repos"] == 3


class TestCacheIntegration:
    """Integration tests for cache with real git operations"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance"""
        return RepositoryCache(cache_dir=temp_cache_dir)

    def test_get_current_commit_hash_in_git_repo(self, cache):
        """Test getting commit hash in actual git repo"""
        commit_hash = cache.get_current_commit_hash()
        # Should return a valid hash (40 chars) or None if not in git repo
        if commit_hash:
            assert isinstance(commit_hash, str)
            assert len(commit_hash) == 40  # SHA-1 hash length

    def test_ttl_default_value(self, cache):
        """Test that TTL defaults to 24 hours"""
        repo_url = "https://github.com/test/repo"
        chunks = [{"id": 1}]
        embeddings = [[0.1]]

        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            cache.save_analysis(repo_url, chunks, embeddings)

        # Should use 24 hour default
        with patch.object(cache, 'get_current_commit_hash', return_value='abc123'):
            assert cache.is_cache_valid(repo_url) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
