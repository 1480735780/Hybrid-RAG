"""
Log Parser - Extract and analyze log files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from rag.parsers.document_parser import BaseParser


class LogParser(BaseParser):
    """
    Log Parser for extracting and analyzing log files.

    Features:
    - Multi-format log support
    - Error detection
    - Log level extraction
    - Timestamp parsing
    """

    # Common log patterns
    LOG_PATTERNS = {
        "syslog": r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(\[\d+\])?:\s+(.*)',
        "apache": r'(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)',
        "nginx": r'(\S+)\s+-\s+\S+\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)',
        "docker": r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(.*)',
        "mysql": r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\d+)\s+\[(\w+)\]\s+(.*)',
    }

    # Error keywords
    ERROR_KEYWORDS = [
        'error', 'exception', 'fatal', 'critical', 'failed',
        'failure', 'panic', 'emergency', 'alert',
    ]

    def parse(self, file_path: str) -> str:
        """
        Parse log file and return content.

        Args:
            file_path: Path to the log file

        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()

        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
            raise

    def parse_with_metadata(self, file_path: str) -> Dict:
        """
        Parse log file and return content with metadata.

        Args:
            file_path: Path to the log file

        Returns:
            Dict with text and metadata
        """
        try:
            path = Path(file_path)
            text = self.parse(file_path)
            lines = text.split('\n')

            # Detect log format
            log_format = self._detect_format(lines)

            # Extract errors
            errors = self._extract_errors(lines)

            # Extract log levels
            log_levels = self._extract_log_levels(lines)

            metadata = {
                "file_path": file_path,
                "file_type": "log",
                "filename": path.name,
                "file_size": path.stat().st_size,
                "total_lines": len(lines),
                "log_format": log_format,
                "error_count": len(errors),
                "errors": errors[:100],  # Limit to first 100 errors
                "log_levels": log_levels,
            }

            return {
                "text": text,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error parsing log file with metadata: {e}")
            raise

    def _detect_format(self, lines: List[str]) -> str:
        """
        Detect log format based on content.

        Args:
            lines: Log lines

        Returns:
            Detected log format
        """
        for line in lines[:100]:  # Check first 100 lines
            for format_name, pattern in self.LOG_PATTERNS.items():
                if re.match(pattern, line):
                    return format_name

        return "unknown"

    def _extract_errors(self, lines: List[str]) -> List[Dict]:
        """
        Extract error lines from log.

        Args:
            lines: Log lines

        Returns:
            List of error entries
        """
        errors = []

        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            for keyword in self.ERROR_KEYWORDS:
                if keyword in line_lower:
                    errors.append({
                        "line_number": line_num,
                        "content": line.strip(),
                        "keyword": keyword,
                    })
                    break

        return errors

    def _extract_log_levels(self, lines: List[str]) -> Dict[str, int]:
        """
        Extract log level statistics.

        Args:
            lines: Log lines

        Returns:
            Dict with log level counts
        """
        levels = {
            "emergency": 0,
            "alert": 0,
            "critical": 0,
            "error": 0,
            "warning": 0,
            "notice": 0,
            "info": 0,
            "debug": 0,
        }

        for line in lines:
            line_upper = line.upper()
            for level in levels.keys():
                if level.upper() in line_upper:
                    levels[level] += 1
                    break

        return levels

    def extract_error_patterns(self, lines: List[str]) -> List[Dict]:
        """
        Extract common error patterns.

        Args:
            lines: Log lines

        Returns:
            List of error patterns
        """
        patterns = []

        # Common error patterns
        error_patterns = [
            (r'ERROR\s+\d+', 'MySQL Error'),
            (r'Exception:\s+(.+)', 'Java Exception'),
            (r'Traceback \(most recent call last\)', 'Python Traceback'),
            (r'segfault\s+at\s+', 'Segmentation Fault'),
            (r'OOM\s+Killer', 'Out of Memory'),
            (r'Connection refused', 'Connection Error'),
            (r'Timeout', 'Timeout Error'),
        ]

        for line in lines:
            for pattern, pattern_name in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    patterns.append({
                        "pattern": pattern_name,
                        "line": line.strip(),
                    })
                    break

        return patterns
