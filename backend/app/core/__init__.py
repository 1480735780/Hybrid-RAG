"""
Core module for backend application.
"""

from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import setup_logging

__all__ = ["register_exception_handlers", "setup_logging"]
