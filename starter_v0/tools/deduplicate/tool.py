from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tools._shared import err


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Each non-empty url must be an absolute HTTP(S) URL")
    if parts.username or parts.password:
        raise ValueError("URLs must not contain credentials")
    query = sorted((key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
                   if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"})
    # Path case and meaningful query parameters remain significant.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(query), ""))


def deduplicate_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first item per canonical URL; keep items without URLs separately."""
    try:
        if items is None:
            raise ValueError("items is required; provide a list (possibly empty)")
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("items must be a list of objects")
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in items:
            url = item.get("url")
            if url is not None and not isinstance(url, str):
                raise ValueError("url must be a string or null")
            key = _canonical_url(url) if url and url.strip() else None
            if key is not None:
                if key in seen:
                    continue
                seen.add(key)
            unique.append(dict(item))
        return {"tool": "deduplicate_items", "items": unique, "input_count": len(items),
                "item_count": len(unique), "removed_count": len(items) - len(unique)}
    except Exception as exc:
        return err("deduplicate_items", exc)
