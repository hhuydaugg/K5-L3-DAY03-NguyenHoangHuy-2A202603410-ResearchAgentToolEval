"""Action boundaries use real user controls, not model-generated flags."""
from unittest.mock import MagicMock

from agent import ResearchAgent
from chat import execute_tool_call, run_model_tool_loop
from conftest import FakeResponse
from providers.base import ModelResponse, ToolCall


def test_model_cannot_confirm_its_own_send(monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    provider = MagicMock()
    provider.complete.return_value = ModelResponse(tool_calls=[ToolCall("send", {"text": "Exact draft", "confirmed": True})])
    result = run_model_tool_loop(provider=provider, messages=[], tools=[], model=None, max_tool_rounds=4)
    assert result["status"] == "waiting_for_user"
    assert result["pending_action"] == {"name": "send", "args": {"text": "Exact draft", "confirmed": True}}
    assert calls == []
    provider.complete.assert_called_once()


def test_explicit_ui_approval_sends_exact_preview(monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    result = execute_tool_call(ToolCall("send", {"text": "Approved draft", "confirmed": True}), allow_send=True)
    assert result["result"]["status"] == "sent"
    assert len(calls) == 1
    assert calls[0]["json"]["text"] == "Approved draft"


def test_eval_scores_raw_send_call_but_cannot_publish(monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    provider = MagicMock()
    call = ToolCall("send", {"text": "Unapproved draft", "confirmed": True})
    provider.complete.return_value = ModelResponse(tool_calls=[call])
    result = ResearchAgent(provider, system_prompt="test").run([{"role": "user", "content": "send it"}])
    assert result.tool_calls == [call]
    assert result.tool_results[0]["result"]["status"] == "needs_confirmation"
    assert calls == []
