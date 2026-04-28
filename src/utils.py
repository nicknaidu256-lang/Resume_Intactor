"""
Utility functions: file I/O helpers, logging setup.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Singleton logger
_logger: Optional[logging.Logger] = None


def setup_logging(log_path: Path, log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging to file and console.

    Args:
        log_path: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is not None:
        return _logger

    # Create logs directory if needed
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("resume_tailor")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # File handler (append mode)
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_fmt)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    if _logger is None:
        return setup_logging(Path("logs/run.log"))
    return _logger


def read_text_file(path: Path, encoding: str = "utf-8") -> str:
    """
    Read entire text file.

    Args:
        path: File path
        encoding: Text encoding

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    """
    logger = get_logger()
    logger.debug(f"Reading file: {path}")
    try:
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        logger.debug(f"Read {len(content)} characters from {path.name}")
        return content
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        raise


def write_text_file(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write text to file, creating directories if needed.

    Args:
        path: Output file path
        content: Text content to write
        encoding: Text encoding
    """
    logger = get_logger()
    logger.debug(f"Writing to file: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        logger.debug(f"Wrote {len(content)} characters to {path}")
    except Exception as e:
        logger.error(f"Failed to write {path}: {e}")
        raise


def ensure_dir_exists(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def timestamp_string() -> str:
    """Generate timestamp string for filenames: YYYYMMDD_HHMMSS."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
