"""
Helper utility functions.
"""

import re
from typing import Optional


def generate_uuid() -> str:
    """Generate a UUID string."""
    from uuid import uuid4
    return str(uuid4())


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing or replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = f"{name[:250]}.{ext}" if ext else name[:255]
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_error_code(text: str) -> Optional[str]:
    """
    Extract error code from text.

    Args:
        text: Text containing error code

    Returns:
        Error code if found, None otherwise
    """
    # Common error code patterns
    patterns = [
        r'ERROR\s+(\d+)',
        r'error[:\s]+(\d+)',
        r'errno[:\s]+(\d+)',
        r'ORA-(\d+)',
        r'MySQL error[:\s]+(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def extract_log_level(text: str) -> Optional[str]:
    """
    Extract log level from log line.

    Args:
        text: Log line

    Returns:
        Log level if found, None otherwise
    """
    levels = ['EMERGENCY', 'ALERT', 'CRITICAL', 'ERROR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG']

    for level in levels:
        if level in text.upper():
            return level

    return None


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    return ' '.join(text.split())
