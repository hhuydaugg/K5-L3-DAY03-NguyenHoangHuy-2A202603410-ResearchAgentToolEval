from __future__ import annotations

import json
import os
import time
import weakref
from typing import Any

from providers.base import ModelResponse, ToolCall


def _retry_delay(exc: Any, attempt: int) -> float | None:
    """Respect server cooldowns; don't wait for daily/zero quotas to recover."""
    if exc.code not in {429, 500, 502, 503, 504}:
        return None
    payload = exc.details if isinstance(exc.details, dict) else {}
    error = payload.get("error", payload)
    delay = 2.0 ** attempt
    retry_hint = False
    for detail in error.get("details", []):
        for violation in detail.get("violations", []):
            quota = str(violation.get("quotaId", "")).lower()
            if "perday" in quota or str(violation.get("quotaValue")) == "0":
                return None
        raw_delay = detail.get("retryDelay")
        if raw_delay is not None:
            try:
                delay = max(delay, float(str(raw_delay).removesuffix("s")) + 0.1)
                retry_hint = True
            except ValueError:
                pass
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) or {}
    try:
        if "retry-after" in headers:
            delay = max(delay, float(headers["retry-after"]) + 0.1)
            retry_hint = True
    except (TypeError, ValueError):
        pass
    if exc.code == 429 and not retry_hint:
        delay = max(delay, 60.1)
    return delay


def _to_gemini_declarations(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    for item in tools or []:
        function = item.get("function", item)
        declarations.append({
            "name": function["name"],
            "description": function.get("description", ""),
            "parameters": function.get("parameters", {"type": "object", "properties": {}}),
        })
    return declarations


def _to_gemini_contents(messages: list[dict[str, str]]) -> tuple[str | None, list[dict[str, Any]]]:
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
    return ("\n\n".join(system_parts) if system_parts else None), contents


def _part_text(part: Any) -> str | None:
    if hasattr(part, "text"):
        return getattr(part, "text")
    if isinstance(part, dict):
        return part.get("text")
    return None


def _part_function_call(part: Any) -> Any | None:
    if hasattr(part, "function_call"):
        return getattr(part, "function_call")
    if isinstance(part, dict):
        return part.get("function_call")
    return None


def _function_call_name(call: Any) -> str | None:
    if hasattr(call, "name"):
        return getattr(call, "name")
    if isinstance(call, dict):
        return call.get("name")
    return None


def _function_call_args(call: Any) -> dict[str, Any]:
    if hasattr(call, "args"):
        return dict(getattr(call, "args") or {})
    if isinstance(call, dict):
        return dict(call.get("args") or {})
    return {}


class GeminiProvider:
    """Google Gemini API provider with normalized tool_calls output."""

    def __init__(
        self,
        *,
        api_key_env: str = "GEMINI_API_KEY",
        default_model: str = "gemini-3.5-flash",
    ) -> None:
        self.api_key_env = api_key_env
        self.default_model = default_model
        # The lab's free tier can allow only five requests per minute.
        self.request_interval = float(os.getenv("GEMINI_REQUEST_INTERVAL", "12.1"))
        if self.request_interval < 0:
            raise ValueError("GEMINI_REQUEST_INTERVAL must be non-negative")
        self._last_request_at: float | None = None
        self._client: Any = None
        self._client_key: str | None = None
        self._client_finalizer: Any = None
        self._blocked_models: dict[str, Any] = {}

    def close(self) -> None:
        if self._client_finalizer is not None:
            self._client_finalizer()
        self._client = None
        self._client_key = None

    def _generate(self, client: Any, **kwargs: Any) -> Any:
        from google.genai.errors import APIError

        selected_model = kwargs["model"]
        if selected_model in self._blocked_models:
            raise self._blocked_models[selected_model]
        retry_at = 0.0
        for attempt in range(4):
            # Tool execution and backoff overlap this interval, rather than
            # adding a full sleep after every case or after every retry.
            interval_at = (self._last_request_at + self.request_interval
                           if self._last_request_at is not None else 0.0)
            remaining = max(interval_at, retry_at) - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            self._last_request_at = time.monotonic()
            try:
                return client.models.generate_content(**kwargs)
            except APIError as exc:
                delay = _retry_delay(exc, attempt)
                if exc.code == 429 and delay is None:
                    # Don't spend another request/interval on each eval case
                    # when this model has already exhausted its daily quota.
                    self._blocked_models[selected_model] = exc
                if attempt == 3 or delay is None:
                    raise
                retry_at = time.monotonic() + delay
                print(f"Gemini HTTP {exc.code}: retry {attempt + 1}/3 in "
                      f"{max(delay, self._last_request_at + self.request_interval - time.monotonic()):.1f}s",
                      flush=True)

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install live provider dependency first: pip install google-genai") from exc

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key env var: {self.api_key_env}")

        system_instruction, contents = _to_gemini_contents(messages)
        declarations = _to_gemini_declarations(tools)
        config_kwargs: dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if declarations:
            config_kwargs["tools"] = [types.Tool(function_declarations=declarations)]

        if self._client is None or self._client_key != api_key:
            self.close()
            self._client = genai.Client(
                api_key=api_key,
                # Handle retries in _generate only, without nested SDK sleeps.
                http_options=types.HttpOptions(timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)),
            )
            self._client_key = api_key
            self._client_finalizer = weakref.finalize(self, self._client.close)
        resp = self._generate(
            self._client,
            model=model or self.default_model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        text_parts: list[str] = []
        calls: list[ToolCall] = []

        def append_call(function_call: Any) -> None:
            name = _function_call_name(function_call)
            if name:
                calls.append(ToolCall(name=name, args=_function_call_args(function_call)))

        for candidate in getattr(resp, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                text = _part_text(part)
                if text:
                    text_parts.append(text)
                function_call = _part_function_call(part)
                if function_call:
                    append_call(function_call)

        # Some SDK versions expose function calls directly on the response.
        for function_call in getattr(resp, "function_calls", []) or []:
            append_call(function_call)

        deduped_calls: list[ToolCall] = []
        seen: set[tuple[str, str]] = set()
        for call in calls:
            key = (call.name, json.dumps(call.args, ensure_ascii=False, sort_keys=True))
            if key not in seen:
                seen.add(key)
                deduped_calls.append(call)

        return ModelResponse(text="\n".join(part for part in text_parts if part) or None, tool_calls=deduped_calls, raw=resp)
