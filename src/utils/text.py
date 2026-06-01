"""Shared text helpers."""

from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """Lowercase, strip accents — used for Vietnamese fuzzy matching."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")
