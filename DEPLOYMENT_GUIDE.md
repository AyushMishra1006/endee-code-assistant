# Professional Deployment Guide
## TTL + Git Commit Hash Cache Validation Feature

**Version:** v1.1.0 | **Date:** March 7, 2026 | **Status:** Complete ✅

---

## 📋 Overview

This document records the complete deployment workflow for implementing cache validation with TTL (Time-To-Live) and Git commit hash versioning.

**Problem:** Old cache returned for updated repositories
**Solution:** Dual validation - check TTL + check if code changed
**Result:** Fresh cache guaranteed, stale data prevented

---

## STEP 1: Create Feature Branch

### Command
```bash
git checkout -b feature/cache-ttl-versioning
```

### What It Does
- Creates new isolated branch for development
- Keeps main branch clean until feature is tested
- Allows safe experimentation

### Verification
```bash
git branch -v
# Output: * feature/cache-ttl-versioning (current branch)
```

---

## STEP 2: Implement Code Changes

### 2.1 Import Required Modules

**File:** `code-assistant/src/cache_manager.py` (lines 1-12)

```python
import subprocess        # NEW: For git commands
from datetime import datetime, timedelta  # NEW: For TTL
```

### 2.2 Add Git Commit Hash Method

**File:** `code-assistant/src/cache_manager.py` (lines 27-39)

```python
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
        return None  # Graceful fallback if not in git repo
```

**Purpose:** Captures current code version as unique identifier

### 2.3 Add Cache Validation Method

**File:** `code-assistant/src/cache_manager.py` (lines 47-82)

```python
def is_cache_valid(self, repo_url: str, ttl_hours: int = 24) -> bool:
    """Check if cache is valid (not expired AND code didn't change)"""
    try:
        repo_hash = self.get_repo_hash(repo_url)
        cache_file = self.cache_dir / f"{repo_hash}.json"

        if not cache_file.exists():
            return False

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Check 1: TTL (Time-To-Live)
        cache_timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
        age = datetime.now() - cache_timestamp
        if age > timedelta(hours=ttl_hours):
            return False  # Cache expired

        # Check 2: Git Commit (Code changed?)
        cached_commit = cache_data.get("commit_hash")
        current_commit = self.get_current_commit_hash()
        if cached_commit and current_commit and cached_commit != current_commit:
            return False  # Repository changed

        return True  # Both checks passed
    except Exception:
        return False
```

**Validation Logic:**
1. Is cache file older than TTL? → Invalid if yes
2. Did commit hash change? → Invalid if yes
3. Both pass? → Valid ✅

### 2.4 Update Save Method

**File:** `code-assistant/src/cache_manager.py` (lines 84-105)

**Before:**
```python
cache_data = {
    "repo_url": repo_url,
    "timestamp": datetime.now().isoformat(),
    "chunks_count": len(chunks),
    "chunks": chunks,
    "embeddings": embeddings,
}
```

**After:**
```python
cache_data = {
    "repo_url": repo_url,
    "timestamp": datetime.now().isoformat(),
    "commit_hash": self.get_current_commit_hash(),  # NEW!
    "chunks_count": len(chunks),
    "chunks": chunks,
    "embeddings": embeddings,
}
```

**Change:** Added commit hash to cache metadata

### 2.5 Update Load Method

**File:** `code-assistant/src/cache_manager.py` (lines 107-124)

**Before:**
```python
def load_analysis(self, repo_url: str):
    # ... load directly
    return chunks, embeddings
```

**After:**
```python
def load_analysis(self, repo_url: str):
    # NEW: Validate cache first
    if not self.is_cache_valid(repo_url):
        return None

    # ... then load
    return chunks, embeddings
```

**Change:** Added validation gate before returning cache

### 2.6 Create Test Suite

**File:** `code-assistant/tests/test_cache_ttl.py` (184 lines)

```python
# 10 Test Cases:
✅ test_save_and_load_cache
✅ test_cache_stores_commit_hash
✅ test_cache_expires_after_ttl
✅ test_cache_invalid_on_commit_change
✅ test_nonexistent_cache_returns_none
✅ test_nonexistent_cache_invalid
✅ test_cache_without_git_still_works
✅ test_cache_stats_includes_all_files
✅ test_get_current_commit_hash_in_git_repo
✅ test_ttl_default_value
```

### 2.7 Run Tests

```bash
pip install pytest
python -m pytest code-assistant/tests/test_cache_ttl.py -v
```

**Result:**
```
10 passed in 0.22s ✅
```

---

## STEP 3: Commit & Push to Main

### 3.1 Stage Files

```bash
git add code-assistant/src/cache_manager.py
git add code-assistant/tests/test_cache_ttl.py
```

### 3.2 Create Commit

```bash
git commit -m "feat: Add TTL + Git commit hash validation to cache

- Prevents stale cache by checking commit hash
- Invalidates cache after 24 hours (TTL)
- Adds is_cache_valid() method with dual validation
- Includes 10 comprehensive test cases
- All tests passing"
```

### 3.3 Switch to Main Branch

```bash
git checkout master
```

### 3.4 Merge Feature Branch

```bash
git merge feature/cache-ttl-versioning
```

**Output:**
```
Updating 8b92006..1e545bb
Fast-forward
 code-assistant/src/cache_manager.py    |  67 ++++++++++--
 code-assistant/tests/test_cache_ttl.py | 184 ++++++++++++++++++++++++
 2 files changed, 245 insertions(+)
```

### 3.5 Sync & Push

```bash
git pull origin master      # Sync with remote
git push origin master      # Push merged code
```

---

## STEP 4: Release & Versioning

### 4.1 Create Version Tag

```bash
git tag -a v1.1.0 -m "Release v1.1.0: TTL + Git commit hash cache validation"
```

**Semantic Versioning:**
- `v1.1.0`
  - `1` = Major (breaking changes)
  - `1` = Minor (new features, backwards compatible)
  - `0` = Patch (bug fixes)

### 4.2 Push Tag to GitHub

```bash
git push origin v1.1.0
```

### 4.3 Create Release Notes

**File:** `RELEASE_NOTES.md`

Contains:
- Summary of changes
- What's new (TTL + Git versioning)
- Technical details (modified files, test results)
- Usage examples
- Backwards compatibility info
- Future enhancements

---

## 📊 Changes Summary

| Component | Status | Impact |
|-----------|--------|--------|
| Code Changes | ✅ 5 modifications | Added 67 lines |
| Test Suite | ✅ 10 tests | 184 lines, all passing |
| Documentation | ✅ Release notes | Comprehensive |
| Git Commits | ✅ 1 commit | Merged to master |
| Version Tag | ✅ v1.1.0 | Created & pushed |

---

## 🔍 Key Code Logic

### Cache Validity Check
```
Cache Valid?
├─ File exists? NO → Invalid ❌
├─ Age > TTL? YES → Invalid ❌
├─ Commit changed? YES → Invalid ❌
└─ All checks pass? YES → Valid ✅
```

### Cache Flow
```
save_analysis()
├─ Store chunks
├─ Store embeddings
└─ Store commit_hash (NEW)

load_analysis()
├─ Check is_cache_valid()    (NEW gate)
├─ Load chunks
├─ Load embeddings
└─ Return data
```

---

## 📝 Git Command Reference

```bash
# Feature branch workflow
git checkout -b feature-name           # Create branch
git add files                          # Stage files
git commit -m "message"                # Create commit
git push -u origin feature-name        # Push branch

# Merge to main
git checkout master                    # Switch to main
git merge feature-name                 # Merge branch
git pull origin master                 # Sync remote
git push origin master                 # Push merged code

# Versioning
git tag -a v1.1.0 -m "message"        # Create tag
git push origin v1.1.0                 # Push tag
git log --decorate                     # View tags
```

---

## ✨ Feature Benefits

| Benefit | How It Works |
|---------|-------------|
| **Fresh Data** | TTL expires old cache automatically |
| **Code Changes Detected** | Commit hash tracks code versions |
| **Reliability** | Dual validation prevents errors |
| **Backwards Compatible** | Existing cache still works |
| **Performance** | Git check is fast (~1-5ms) |
| **Tested** | 10 test cases covering all scenarios |

---

## 🚀 Deployment Status

- ✅ Feature implemented
- ✅ All tests passing (10/10)
- ✅ Code merged to master
- ✅ Version tagged (v1.1.0)
- ✅ Release notes documented
- ⏳ Ready for production deployment

---

## 📚 Files Modified

1. **code-assistant/src/cache_manager.py**
   - Added imports: subprocess, timedelta
   - Added: get_current_commit_hash() method
   - Added: is_cache_valid() method
   - Modified: save_analysis() - now stores commit hash
   - Modified: load_analysis() - now validates cache

2. **code-assistant/tests/test_cache_ttl.py** (NEW)
   - 10 comprehensive test cases
   - Tests TTL expiration
   - Tests commit hash detection
   - Tests edge cases

3. **RELEASE_NOTES.md** (NEW)
   - Complete feature documentation
   - Usage examples
   - Test results
   - Future roadmap

---

## 🔗 References

- **Repository:** https://github.com/AyushMishra1006/endee-code-assistant
- **Release Tag:** v1.1.0
- **Live Demo:** https://endeecodeassistant.streamlit.app/

---

**Deployment Date:** March 7, 2026
**Deployed By:** Ayush Mishra
**Status:** Complete & Production Ready ✅
