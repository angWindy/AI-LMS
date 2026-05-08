"""Pytest collection rules for RAG smoke scripts."""

# These files are command-line smoke scripts, not pytest modules. They execute
# work at import time, so collecting them under pytest can trigger side effects
# or SystemExit before the real function-based tests run.
collect_ignore = [
    "test_integration.py",
    "test_rag_comprehensive.py",
    "test_standalone.py",
]
