from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools._shared import err, require_items


def _date_sort_key(item: dict[str, Any]) -> tuple[int, float, str]:
    raw = item.get("date")
    if raw is None or not str(raw).strip():
        return (1, 0.0, "")
    text = str(raw).strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return (0, -parsed.timestamp(), "")
    except (ValueError, OSError, TypeError, OverflowError):
        return (1, 0.0, text.lower())


def _nonneg_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError("limit must be a non-negative integer")
    if isinstance(value, str):
        value = int(value.strip())
    elif isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int) or value < 0:
        raise ValueError("limit must be a non-negative integer")
    return value


def rank_items(items: list[dict[str, Any]] | None = None, by: str = "date", limit: int = 0) -> dict[str, Any]:
    try:
        items = require_items(items)
        if by not in {"date", "title"}:
            raise ValueError("by must be date or title")
        limit = _nonneg_int(limit)
        ranked = [dict(item) for item in items]
        if by == "title":
            ranked.sort(key=lambda item: str(item.get("title") or "").lower())
        else:
            ranked.sort(key=_date_sort_key)
        if limit:
            ranked = ranked[:limit]
        return {"tool": "rank_items", "by": by, "items": ranked, "item_count": len(ranked)}
    except Exception as exc:
        return err("rank_items", exc)
