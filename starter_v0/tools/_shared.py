from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 30


def err(tool: str, exc: Exception) -> dict[str, Any]:
    return {"tool": tool, "error": type(exc).__name__, "message": str(exc)}


def require_items(items: Any) -> list[dict[str, Any]]:
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except json.JSONDecodeError as exc:
            raise ValueError("items must be a list of objects") from exc
    if items is None:
        raise ValueError("items is required; provide a list (possibly empty)")
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError("items must be a list of objects")
    return items


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def fold_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def terms(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to",
        "ban", "bao", "can", "cho", "co", "cua", "duoc", "gi", "giup", "la", "lam", "minh", "mot", "nay",
        "nen", "the", "thi", "trong", "va", "ve", "voi",
    }
    folded = fold_text(text)
    return {term for term in re.findall(r"[a-z0-9]+", folded) if len(term) > 1 and term not in stopwords}

