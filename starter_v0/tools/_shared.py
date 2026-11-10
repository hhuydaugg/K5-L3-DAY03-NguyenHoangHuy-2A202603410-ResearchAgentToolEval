from __future__ import annotations

import re
import os
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 30


def err(tool: str, exc: Exception) -> dict[str, Any]:
    message = str(exc)
    for key, value in os.environ.items():
        if value and len(value) > 8 and (key.endswith("_KEY") or key.endswith("_TOKEN")):
            message = message.replace(value, "[REDACTED]")
    message = re.sub(r"(api\.telegram\.org/bot)[^/\s]+", r"\1[REDACTED]", message)
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if status is None:
        match = re.search(r"(?:HTTP\s+|^)([45]\d{2})(?:\s|$)", message)
        status = int(match.group(1)) if match else None
    retryable = status == 429 or (isinstance(status, int) and status >= 500) or "timeout" in type(exc).__name__.lower() or isinstance(exc, TimeoutError) or bool(re.search(r"timed? out|timeout", message, re.I))
    return {"tool": tool, "error": type(exc).__name__, "message": message,
            "status_code": status, "retryable": retryable}


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

