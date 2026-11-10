from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def read_url(url: str = "") -> dict[str, Any]:
    try:
        key = os.getenv("FIRECRAWL_API_KEY")
        if not key:
            raise RuntimeError("Missing FIRECRAWL_API_KEY env var")
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("success") is False:
            raise RuntimeError("Scrape provider reported failure")
        data = payload.get("data", {}) or {}
        meta = data.get("metadata", {}) or {}
        status = meta.get("statusCode") or meta.get("status_code")
        if status is not None and int(status) >= 400:
            return {"tool": "read_url", "error": "SourceHTTPError", "status_code": int(status),
                    "message": "The target page returned an HTTP error; content is not usable.",
                    "retryable": int(status) == 429 or int(status) >= 500}
        if not isinstance(data.get("markdown"), str) or not data["markdown"].strip():
            return {"tool": "read_url", "error": "EmptyContent", "message": "No readable page content was returned.",
                    "status_code": status, "retryable": False}
        return {"tool": "read_url", "url": url, "items": [{
            "title": meta.get("title") or url,
            "url": meta.get("sourceURL") or url,
            "source": domain(url),
            "summary": (data.get("markdown") or "")[:4000],
        }]}
    except Exception as exc:
        return err("read_url", exc)

