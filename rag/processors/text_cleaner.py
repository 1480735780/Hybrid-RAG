"""
Text Cleaner - Clean and normalize text for RAG processing.
"""

import re
from typing import Optional

from loguru import logger


class TextCleaner:
    """
    Text Cleaner for cleaning and normalizing text.

    Features:
    - Whitespace normalization
    - Unicode normalization
    - Special character handling
    - Encoding issue fixing
    """

    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_special_chars: bool = False,
        lowercase: bool = False,
    ):
        """
        Initialize text cleaner.

        Args:
            remove_extra_whitespace: Whether to remove extra whitespace
            normalize_unicode: Whether to normalize unicode
            remove_special_chars: Whether to remove special characters
            lowercase: Whether to convert to lowercase
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_special_chars = remove_special_chars
        self.lowercase = lowercase

    def clean(self, text: str) -> str:
        """
        Clean text.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Fix encoding issues
        text = self._fix_encoding(text)

        # Normalize unicode
        if self.normalize_unicode:
            text = self._normalize_unicode(text)

        # Remove extra whitespace
        if self.remove_extra_whitespace:
            text = self._normalize_whitespace(text)

        # Remove special characters
        if self.remove_special_chars:
            text = self._remove_special_chars(text)

        # Convert to lowercase
        if self.lowercase:
            text = text.lower()

        return text.strip()

    def _fix_encoding(self, text: str) -> str:
        """
        Fix common encoding issues.

        Args:
            text: Text to fix

        Returns:
            Fixed text
        """
        # Common encoding fixes
        replacements = {
            '‘': "'",  # Left single quote
            '’': "'",  # Right single quote
            '“': '"',  # Left double quote
            '”': '"',  # Right double quote
            '–': '-',  # En dash
            '—': '-',  # Em dash
            '…': '...',  # Ellipsis
            '\xa0': ' ',  # Non-breaking space
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        import unicodedata

        # Normalize to NFC form
        text = unicodedata.normalize('NFC', text)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)

        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text

    def _remove_special_chars(self, text: str) -> str:
        """
        Remove special characters.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Keep alphanumeric, whitespace, and basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)

        return text

    def clean_for_embedding(self, text: str) -> str:
        """
        Clean text specifically for embedding generation.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Basic cleaning
        text = self.clean(text)

        # Additional cleaning for embeddings
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]*`', '', text)

        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'#+\s+', '', text)

        return text.strip()

    def clean_for_bm25(self, text: str) -> str:
        """
        Clean text specifically for BM25 search.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Basic cleaning
        text = self.clean(text)

        # Keep important technical terms
        # Don't remove special characters that might be in error codes
        # e.g., ERROR 2002, mysqld.sock, nginx.conf

        return text

    def extract_error_messages(self, text: str) -> list:
        """
        Extract error messages from text.

        Args:
            text: Text to extract from

        Returns:
            List of error messages
        """
        error_patterns = [
            r'ERROR\s*[:]\s*(.+)',
            r'Exception\s*[:]\s*(.+)',
            r'FATAL\s*[:]\s*(.+)',
            r'CRITICAL\s*[:]\s*(.+)',
            r'Failed\s*[:]\s*(.+)',
        ]

        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            errors.extend(matches)

        return errors
