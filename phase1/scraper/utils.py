"""
Phase 1 — Utility functions: logging, retry logic, text cleaning helpers.
"""

import logging
import time
import re
from functools import wraps
from pathlib import Path


# ─── Logger Setup ───────────────────────────────────────────────────
def get_logger(name: str = "phase1") -> logging.Logger:
    """Create a configured logger for Phase 1."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        # File handler
        log_dir = Path("phase1/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / "scraper.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


logger = get_logger()


# ─── Retry Decorator ───────────────────────────────────────────────
def retry(max_attempts: int = 3, delay_sec: float = 5.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait = delay_sec * (backoff ** (attempt - 1))
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception  # type: ignore
        return wrapper
    return decorator


# ─── Text Cleaning Helpers ──────────────────────────────────────────
def clean_text(text: str | None) -> str:
    """Strip whitespace, normalize spaces, remove invisible chars."""
    if not text:
        return ""
    # Remove zero-width chars and normalize whitespace
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_percentage(text: str | None) -> str | None:
    """Extract percentage value from text like '0.8%' or '0.80 %'."""
    if not text:
        return None
    match = re.search(r'([\d.]+)\s*%', text)
    if match:
        return f"{match.group(1)}%"
    return clean_text(text)


def clean_currency(text: str | None) -> str | None:
    """Extract currency value from text like '₹19.18' or '₹ 4,486 Cr'."""
    if not text:
        return None
    text = clean_text(text)
    # Remove currency symbol but keep the rest
    text = re.sub(r'[₹$]', '', text).strip()
    return text if text else None


def parse_nav(text: str | None) -> str | None:
    """Extract NAV numeric value from text like '₹19.18'."""
    if not text:
        return None
    match = re.search(r'₹?\s*([\d,.]+)', text)
    if match:
        return f"₹{match.group(1)}"
    return clean_text(text)


def extract_number(text: str | None) -> float | None:
    """Extract first numeric value from text."""
    if not text:
        return None
    match = re.search(r'([\d,.]+)', text.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def safe_get(data: dict, *keys, default=None):
    """Safely navigate nested dict keys."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def ensure_dir(path: str | Path) -> Path:
    """Create directory if it doesn't exist and return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
