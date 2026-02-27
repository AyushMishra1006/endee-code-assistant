"""
Utility functions for Code Documentation Assistant
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import git

# Constants
MAX_REPO_SIZE = 100 * 1024 * 1024  # 100MB hard limit
CLONE_TIMEOUT = 60  # seconds


def validate_github_url(url: str) -> bool:
    """Validate GitHub URL format"""
    return url.startswith("https://github.com/") and (url.endswith(".git") or url.count("/") >= 4)


def get_repo_size(path: str) -> int:
    """Get total size of directory in bytes"""
    total = 0
    for entry in os.scandir(path):
        if entry.is_file(follow_symlinks=False):
            total += entry.stat().st_size
        elif entry.is_dir(follow_symlinks=False):
            total += get_repo_size(entry.path)
    return total


def clone_repository(repo_url: str) -> tuple[str, Optional[str]]:
    """
    Clone GitHub repository to temporary directory

    Args:
        repo_url: GitHub repository URL

    Returns:
        Tuple of (temp_directory, error_message)
        If successful, error_message is None
    """
    # Validate URL
    if not validate_github_url(repo_url):
        return None, "Invalid GitHub URL. Expected: https://github.com/user/repo or https://github.com/user/repo.git"

    # Ensure .git suffix
    if not repo_url.endswith(".git"):
        repo_url += ".git"

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="code_assistant_")

    try:
        # Clone repo (remove timeout - not supported by GitPython)
        git.Repo.clone_from(repo_url, temp_dir, depth=1)

        # Check size
        repo_size = get_repo_size(temp_dir)
        if repo_size > MAX_REPO_SIZE:
            cleanup_repo(temp_dir)
            size_mb = repo_size / (1024 * 1024)
            return None, f"Repository too large ({size_mb:.0f}MB). Maximum allowed: 100MB"

        return temp_dir, None

    except git.exc.GitCommandError as e:
        cleanup_repo(temp_dir)
        return None, f"Failed to clone repository: {str(e)}"
    except Exception as e:
        cleanup_repo(temp_dir)
        return None, f"Error during cloning: {str(e)}"


def cleanup_repo(path: str) -> None:
    """Remove temporary repository directory"""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except Exception as e:
            print(f"Warning: Could not cleanup {path}: {e}")


def find_python_files(root_path: str) -> list[str]:
    """Find all Python files in directory"""
    python_files = []
    for root, dirs, files in os.walk(root_path):
        # Skip common non-code directories
        dirs[:] = [d for d in dirs if d not in [
            '__pycache__', '.git', '.venv', 'venv', 'node_modules', '.egg-info'
        ]]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return python_files
