"""
Re-export app from app.main for backward compatibility.
"""
from app.main import app

__all__ = ["app"]