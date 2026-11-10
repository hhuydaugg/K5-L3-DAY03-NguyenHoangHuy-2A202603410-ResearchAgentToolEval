from __future__ import annotations

from typing import Any

from tools._shared import domain, err, require_items


def list_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    try:
        items = require_items(items)
        sources: list[str] = []
        seen: set[str] = set()
        for item in items:
            name = domain(str(item.get("url") or "")) or str(item.get("source") or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            sources.append(name)
        return {"tool": "list_sources", "sources": sources, "source_count": len(sources),
                "input_count": len(items)}
    except Exception as exc:
        return err("list_sources", exc)
