"""Backend app package initialization."""
import os
import sys

# Add the /app or repo root to sys.path safely
try:
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_str = str(repo_root)
    if os.path.exists(repo_root_str) and repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
except IndexError:
    pass
