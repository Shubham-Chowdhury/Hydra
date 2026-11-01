"""Deterministic Normalisation Utilities for Admissions Ingestion (Phase 3).

Ensures all text fields, institute names, programme titles, quotas, categories,
and rank strings are converted to canonical deterministic forms without silent data loss.
"""

import re
from typing import Any, Optional, Tuple


def normalize_whitespace(text: Optional[str]) -> str:
    """Strips leading/trailing whitespace and compresses consecutive spaces."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def normalize_institution_id(name: str) -> str:
    """Generates a stable, canonical institution identifier from its official published name."""
    clean = normalize_whitespace(name).upper()
    # Replace non-alphanumeric with underscore
    clean = re.sub(r"[^A-Z0-9]+", "_", clean).strip("_")
    return f"INST_{clean}"


def normalize_programme_id(institution_id: str, programme_title: str) -> str:
    """Generates a stable programme identifier scoped to the institution."""
    clean_prog = normalize_whitespace(programme_title).upper()
    clean_prog = re.sub(r"[^A-Z0-9]+", "_", clean_prog).strip("_")
    return f"{institution_id}_PROG_{clean_prog[:40]}"


def normalize_quota(quota: str) -> str:
    """Normalises counselling quota codes (e.g., AI, HS, OS, JK, LA, GO)."""
    return normalize_whitespace(quota).upper()


def normalize_seat_type(seat_type: str) -> str:
    """Normalises reservation and seat categories to standard JoSAA naming."""
    clean = normalize_whitespace(seat_type).upper()
    # Canonicalize EWS variants
    if clean in ("EWS", "GEN-EWS", "GENERAL-EWS"):
        return "GEN-EWS"
    if clean in ("EWS (PWD)", "GEN-EWS (PWD)", "GENERAL-EWS (PWD)"):
        return "GEN-EWS (PwD)"
    if clean in ("OPEN (PWD)", "OPEN-PWD"):
        return "OPEN (PwD)"
    if clean in ("OBC-NCL (PWD)", "OBC-NCL-PWD"):
        return "OBC-NCL (PwD)"
    if clean in ("SC (PWD)", "SC-PWD"):
        return "SC (PwD)"
    if clean in ("ST (PWD)", "ST-PWD"):
        return "ST (PwD)"
    return clean


def normalize_gender_pool(gender: str) -> str:
    """Maps varied gender pool representations to canonical JoSAA categories."""
    clean = normalize_whitespace(gender).lower()
    if "female" in clean:
        return "Female-only (including Supernumerary)"
    return "Gender-Neutral"


def parse_rank_value(raw_rank: Any) -> Tuple[Optional[int], str]:
    """Parses raw rank input into an integer rank and identified rank basis.

    Returns:
        Tuple[Optional[int], str]: (parsed_rank, rank_basis)
        where rank_basis is "CRL", "CATEGORY_RANK", or "PREPARATORY".
    """
    if raw_rank is None:
        return None, "UNKNOWN"

    raw_str = str(raw_rank).strip().replace(",", "")
    if not raw_str:
        return None, "UNKNOWN"

    # Check for preparatory ranks (e.g., "12P", "145P")
    if raw_str.upper().endswith("P"):
        try:
            num = int(raw_str[:-1])
            return num, "PREPARATORY"
        except ValueError:
            return None, "INVALID"

    try:
        val = int(raw_str)
        return val, "STANDARD"
    except ValueError:
        return None, "INVALID"
