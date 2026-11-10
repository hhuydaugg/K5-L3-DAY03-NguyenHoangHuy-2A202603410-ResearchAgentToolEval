from __future__ import annotations

from typing import Any

from tools._shared import err, fold_text, require_items


def filter_items(items: list[dict[str, Any]] | None = None, query: str = "") -> dict[str, Any]:
    try:
        items = require_items(items)
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        needle = fold_text(query)
        kept = []
        for item in items:
            haystack = " ".join(str(item.get(field) or "") for field in ("title", "summary", "url", "source"))
            if needle in fold_text(haystack):
                kept.append(dict(item))
        return {"tool": "filter_items", "query": query, "items": kept,
                "input_count": len(items), "item_count": len(kept)}
    except Exception as exc:
        return err("filter_items", exc)
