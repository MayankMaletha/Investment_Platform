"""utils/helpers.py — Shared utility functions."""

import re
from decimal import Decimal
from typing import Any, Optional


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value)) if value is not None else default
    except Exception:
        return default


def truncate_text(text: str, max_length: int = 500) -> str:
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_currency(amount: float, currency: str = "USD") -> str:
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def format_percentage(value: float) -> str:
    return f"{value:+.2f}%"


def clean_symbol(symbol: str) -> str:
    """Sanitize a ticker symbol."""
    return re.sub(r"[^A-Z0-9\-\.]", "", symbol.upper())[:20]


def calculate_percentage_change(old_val: float, new_val: float) -> Optional[float]:
    if not old_val or old_val == 0:
        return None
    return round((new_val - old_val) / old_val * 100, 4)
