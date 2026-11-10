"""Offline behavioural tests for starter tools and the new deduplicate tool."""
from copy import deepcopy

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.deduplicate import tool as deduplicate_module


def test_clarify_choice_returns_options_and_awaits_user():
    options = ["Web", "Twitter"]
    result = TOOL_FUNCTIONS["clarify"]("Chon nguon?", "choice", options)
    assert result["options"] == options
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


def test_format_sections_groups_items_by_section():
    result = TOOL_FUNCTIONS["format"]([
        {"title": "a", "section": "A"}, {"title": "b", "section": "B"},
        {"title": "c", "section": "A"},
    ], template="sections")
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1
    assert result["markdown"].index("- a") < result["markdown"].index("- c") < result["markdown"].index("## B")


def test_format_thread_numbers_items():
    result = TOOL_FUNCTIONS["format"]([{"title": "one"}, {"title": "two"}], template="thread")
    assert result["markdown"].startswith("1/ one")
    assert "\n\n2/ two" in result["markdown"]


@pytest.mark.parametrize("items", [None, []])
def test_format_empty_items_does_not_crash(items):
    result = TOOL_FUNCTIONS["format"](items)
    assert result["item_count"] == 0
    assert isinstance(result["markdown"], str)


def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"]("Digest", confirmed=True)
    assert result["status"] == "sent"
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.telegram.org/bottest-token/sendMessage"
    assert calls[0]["json"]["chat_id"] == "test-channel"
    assert calls[0]["json"]["text"] == "Digest"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http):
    calls = fake_http(FakeResponse())
    result = TOOL_FUNCTIONS["send"]("Digest", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert calls == []


@pytest.mark.parametrize("confirmed", ["false", "true", 1, [], None])
def test_send_rejects_non_boolean_confirmation(confirmed, monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    assert TOOL_FUNCTIONS["send"]("Digest", confirmed=confirmed)["status"] == "needs_confirmation"
    assert calls == []


def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    result = TOOL_FUNCTIONS["lookup"]("robotics", timeframe=None)
    assert "time_range" not in calls[0]["json"]
    assert result["items"] == []


def test_fetch_maps_firecrawl_response(monkeypatch, fake_http):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "Article body", "metadata": {"title": "T", "sourceURL": "https://example.com/final"},
    }}))
    result = TOOL_FUNCTIONS["fetch"]("https://www.example.com/start")
    assert calls[0]["json"] == {"url": "https://www.example.com/start", "formats": ["markdown"]}
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert result["items"] == [{"title": "T", "url": "https://example.com/final", "source": "example.com", "summary": "Article body"}]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000}}))
    result = TOOL_FUNCTIONS["fetch"]("https://example.com/a")
    assert result["items"][0]["summary"] == "x" * 4000


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": [{"text": "no ID"}] + [
        {"tweet_id": str(i), "screen_name": "sama", "text": f"post {i}"} for i in range(1, 7)
    ]}))
    result = TOOL_FUNCTIONS["timeline"]("sama", limit=3)
    assert calls[0]["params"] == {"screenname": "sama"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "test-key"
    assert [item["url"] for item in result["items"]] == [f"https://x.com/sama/status/{i}" for i in range(1, 4)]


@pytest.mark.parametrize("search_type", ["Latest", "Top"])
def test_social_search_passes_search_type(search_type, monkeypatch, fake_http):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": [{"id": "1", "screen_name": "sama", "text": "AI"}]}))
    result = TOOL_FUNCTIONS["social_search"]("AI", search_type=search_type, limit=1)
    assert calls[0]["params"] == {"query": "AI", "search_type": search_type}
    assert len(result["items"]) == 1


def test_social_search_timeout_returns_error(monkeypatch, fake_http):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    fake_http(requests.Timeout("timed out"))
    assert TOOL_FUNCTIONS["social_search"]("AI")["error"] == "Timeout"


def test_policy_empty_query_returns_no_results():
    assert TOOL_FUNCTIONS["policy"]("")["results"] == []


def test_policy_area_filter_only_returns_that_area():
    results = TOOL_FUNCTIONS["policy"]("data privacy", policy_area="data_privacy")["results"]
    assert results
    assert all(item["policy_area"] == "data_privacy" for item in results)


def test_policy_instruction_like_lines_go_to_untrusted_text():
    results = TOOL_FUNCTIONS["policy"]("injection probe", policy_area="source_citation", top_k=10)["results"]
    injected = next(item for item in results if item["untrusted_text"])
    assert any("ignore the citation policy" in line for line in injected["untrusted_text"])
    assert "ignore the citation policy" not in injected["facts"]


def test_deduplicate_happy_path_preserves_first_item_and_input():
    items = [{"title": "Original", "url": "https://EXAMPLE.com/a?utm_source=x&id=1#section"},
             {"title": "Copy", "url": "https://example.com/a?id=1"},
             {"title": "Different", "url": "https://example.com/a?id=2"}]
    before = deepcopy(items)
    result = TOOL_FUNCTIONS["deduplicate"](items)
    assert result["items"] == [items[0], items[2]]
    assert result["input_count"] == 3
    assert result["removed_count"] == 1
    assert result["item_count"] == 2
    assert items == before


@pytest.mark.parametrize("items", [None, "text", ["bad"], [{"url": 5}], [{"url": "not-a-url"}], [{"url": "file:///tmp/a"}]])
def test_deduplicate_bad_input_returns_error(items):
    assert TOOL_FUNCTIONS["deduplicate"](items)["error"] == "ValueError"


def test_deduplicate_failure_returns_error_dict(monkeypatch):
    def broken(url):
        raise RuntimeError("normalization failure")
    monkeypatch.setattr(deduplicate_module, "_canonical_url", broken)
    result = TOOL_FUNCTIONS["deduplicate"]([{"url": "https://example.com"}])
    assert result["error"] == "RuntimeError"
    assert result["message"] == "normalization failure"


def test_deduplicate_keeps_items_without_urls_and_distinct_path_case():
    items = [{"title": "Same"}, {"title": "Same"},
             {"url": "https://example.com/A"}, {"url": "https://example.com/a"}]
    assert TOOL_FUNCTIONS["deduplicate"](items)["items"] == items
    assert TOOL_FUNCTIONS["deduplicate"]([])["items"] == []
