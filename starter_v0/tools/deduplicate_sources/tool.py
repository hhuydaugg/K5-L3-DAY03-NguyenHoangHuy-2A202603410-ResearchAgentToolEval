from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from tools._shared import err


def deduplicate_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first item for each exact stripped HTTP(S) URL; never mutate input."""
    try:
        if not isinstance(items, list):
            raise ValueError("items must be a list of source objects")
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                raise ValueError(f"items[{index}] must contain a string url")
            url = item["url"].strip()
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(c.isspace() for c in url):
                raise ValueError(f"items[{index}] needs an absolute HTTP(S) URL without whitespace")
            if url not in seen:
                seen.add(url)
                unique.append({**item, "url": url})
        return {"tool": "deduplicate_sources", "items": unique,
                "item_count": len(unique), "removed_count": len(items) - len(unique)}
    except Exception as exc:
        return err("deduplicate_sources", exc)
