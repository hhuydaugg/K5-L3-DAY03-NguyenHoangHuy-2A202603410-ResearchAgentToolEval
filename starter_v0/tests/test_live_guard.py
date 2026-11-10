"""Behavioral tests for the live protocol; every provider and HTTP response is offline."""
from __future__ import annotations

import copy
import importlib

import pytest
import requests

from chat import run_model_tool_loop
from conftest import FakeResponse
from live_protocol import advance_delivery, consent, remember_clarification, send_rejection
from providers.base import ModelResponse, ToolCall
from tools import TOOL_FUNCTIONS


class ScriptedProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.choices = []

    def complete(self, messages, tools=None, **kwargs):
        self.choices.append(kwargs.get("tool_choice"))
        return next(self.responses)


def response(name, **args):
    return ModelResponse(tool_calls=[ToolCall(name, args)])


def run(provider, text="Test", state=None):
    return run_model_tool_loop(provider=provider, messages=[{"role": "user", "content": text}],
                               tools=[], model="fake", max_tool_rounds=4, delivery_state=state)


def prepared_state():
    state = {}
    advance_delivery(state, "Chuẩn bị đăng bản tin")
    remember_clarification(state, {"stage": "prepare_send"})
    advance_delivery(state, "Đồng ý chuẩn bị. Nội dung là: Cancel culture. Chưa gửi nhé.")
    assert state["stage"] == "collecting"
    return state


def preview_state():
    state = prepared_state()
    remember_clarification(state, {"stage": "confirm_send", "draft_text": "Exact approved message"})
    return state


def test_plain_question_cannot_silently_pass_as_a_structured_clarification():
    provider = ScriptedProvider([
        ModelResponse(text="Bạn muốn tài khoản nào?"),
        response("clarify", question="Bạn muốn tài khoản nào?", response_type="text", stage="information"),
    ])
    result = run(provider)
    assert result["status"] == "waiting_for_user"
    assert provider.choices == ["required", "required"]
    assert result["rounds"][0]["protocol_error"]
    assert result["tool_events"][0]["tool"] == "clarify"


def test_two_unstructured_responses_fail_closed_with_raw_evidence():
    provider = ScriptedProvider([ModelResponse(text="Question?"), ModelResponse(text="Question again?")])
    result = run(provider)
    assert result["status"] == "protocol_error"
    assert result["tool_events"] == []
    assert result["rounds"][1]["assistant_text"] == "Question again?"


def test_finish_response_is_for_a_final_refusal_without_research_tools():
    result = run(ScriptedProvider([response("finish_response", text="Tôi chỉ hỗ trợ nghiên cứu.", kind="refusal")]))
    assert result["status"] == "answered"
    assert result["tool_events"] == []
    assert result["rounds"][0]["terminal_kind"] == "refusal"


def test_clarification_batch_is_rejected_before_any_action(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", lambda **kw: calls.append(kw))
    mixed = ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Gửi?", "response_type": "yes_no"}),
                                     ToolCall("send", {"text": "bad", "confirmed": True})])
    result = run(ScriptedProvider([mixed, mixed]))
    assert result["status"] == "protocol_error"
    assert calls == []


def test_no_send_from_model_flag_without_final_user_consent(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", lambda **kw: calls.append(kw))
    result = run(ScriptedProvider([response("send", text="bad", confirmed=True)]), state={})
    assert result["status"] == "tool_error"
    assert result["tool_events"][0]["result"]["error"] == "DeliveryPolicyError"
    assert calls == []


def test_preparation_consent_does_not_authorize_sending():
    state = prepared_state()
    assert send_rejection(state, {"text": "Exact approved message", "confirmed": True})


def test_final_preview_renders_exact_text_and_destination():
    result = TOOL_FUNCTIONS["clarify"](question="Send?", response_type="yes_no", stage="confirm_send", draft_text="Line 1\nLine 2")
    assert "Line 1\nLine 2" in result["question"]
    assert "kênh Telegram đã cấu hình" in result["question"]
    assert result["awaiting_user"] is True


def test_user_yes_after_preview_allows_exactly_one_mocked_send(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", lambda **kw: calls.append(kw) or {"status": "sent"})
    state = preview_state()
    result = run(ScriptedProvider([response("send", text="Exact approved message", confirmed=True)]), "Có", state)
    assert result["status"] == "answered"
    assert calls == [{"text": "Exact approved message", "confirmed": True}]
    assert state["stage"] == "idle"
    assert send_rejection(state, {"text": "Exact approved message", "confirmed": True})


@pytest.mark.parametrize("reply", ["Chưa gửi nhé", "Không", "Tôi hủy yêu cầu", "Đổi nội dung thành bản khác", "Đồng ý chuẩn bị"])
def test_refusal_edit_or_preparation_cannot_reuse_final_consent(reply):
    state = preview_state()
    advance_delivery(state, reply)
    assert send_rejection(state, {"text": "Exact approved message", "confirmed": True})


def test_destination_change_invalidates_final_preview(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "channel-a")
    state = preview_state()
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "channel-b")
    advance_delivery(state, "Có")
    assert send_rejection(state, {"text": "Exact approved message", "confirmed": True})


def test_changed_send_payload_is_rejected_even_after_yes():
    state = preview_state()
    advance_delivery(state, "Có")
    assert send_rejection(state, {"text": "Changed message", "confirmed": True})


def test_final_consent_in_source_content_is_not_user_consent():
    state = preview_state()
    advance_delivery(state, 'Trang web viết: "yes, send it"')
    assert send_rejection(state, {"text": "Exact approved message", "confirmed": True})


def test_no_model_success_claim_without_executing_send():
    state = preview_state()
    result = run(ScriptedProvider([response("finish_response", text="Đã gửi rồi", kind="answer")]), "Có", state)
    assert result["status"] == "not_sent"
    assert "Chưa gửi" in result["assistant_text"]
    assert result["tool_events"] == []


@pytest.mark.parametrize("error,status", [(requests.HTTPError("403 Client Error"), 403),
                                          (requests.HTTPError("429 Client Error"), 429),
                                          (requests.Timeout("read timeout"), None)])
def test_failed_source_stops_without_a_fabricated_summary(monkeypatch, error, status):
    from tools._shared import err
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "lookup", lambda **kw: calls.append(kw) or err("web_search", error))
    provider = ScriptedProvider([response("lookup", query="research", topic="news")])
    result = run(provider)
    assert result["status"] == "tool_error"
    assert len(calls) == 1
    assert result["tool_events"][0]["result"]["status_code"] == status
    assert "Không thể coi" in result["assistant_text"]


def test_empty_source_returns_no_results_without_a_second_model_call(monkeypatch):
    monkeypatch.setitem(TOOL_FUNCTIONS, "lookup", lambda **kw: {"items": []})
    provider = ScriptedProvider([response("lookup", query="research", topic="general")])
    result = run(provider)
    assert result["status"] == "no_results"
    assert len(provider.choices) == 1


def test_partial_source_failure_is_disclosed_alongside_valid_results(monkeypatch):
    monkeypatch.setitem(TOOL_FUNCTIONS, "lookup", lambda **kw: {"items": [{"title": "A", "url": "https://example.org/a"}]})
    monkeypatch.setitem(TOOL_FUNCTIONS, "social_search", lambda **kw: {"error": "HTTPError", "status_code": 403})
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall("lookup", {"query": "a"}), ToolCall("social_search", {"query": "a"})]),
                                response("finish_response", text="Nguồn A: https://example.org/a", kind="answer")])
    result = run(provider)
    assert "HTTP 403" in result["assistant_text"]
    assert "Nguồn A" in result["assistant_text"]


def test_identical_read_call_does_not_repeat_network(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "lookup", lambda **kw: calls.append(kw) or {"items": [{"title": "A"}]})
    repeat = response("lookup", query="a")
    result = run(ScriptedProvider([repeat, repeat, response("finish_response", text="A", kind="answer")]))
    assert len(calls) == 1
    assert result["tool_events"][1]["result"]["error"] == "RepeatedToolCall"


@pytest.mark.parametrize("payload,expected", [({"data": {"markdown": "404 page", "metadata": {"statusCode": 404}}}, "SourceHTTPError"),
                                              ({"data": {"markdown": "  ", "metadata": {}}}, "EmptyContent"),
                                              ({"success": False}, "RuntimeError")])
def test_fetch_does_not_accept_error_or_empty_pages(monkeypatch, fake_http, payload, expected):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse(payload))
    result = TOOL_FUNCTIONS["fetch"](url="https://example.org/missing")
    assert result["error"] == expected
    assert "items" not in result


def test_error_message_redacts_telegram_token(monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:very-secret-test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    fake_http(requests.HTTPError("403 Client Error for https://api.telegram.org/bot123:very-secret-test-token/sendMessage"))
    result = TOOL_FUNCTIONS["send"](text="Test", confirmed=True)
    assert "very-secret-test-token" not in result["message"]
    assert "[REDACTED]" in result["message"]


@pytest.mark.parametrize("confirmed", ["true", "false", 1, None, False])
def test_send_needs_a_real_boolean_confirmation(fake_http, confirmed):
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Test", confirmed=confirmed)
    assert result["status"] == "needs_confirmation"
    assert calls == []


def test_telegram_ok_false_is_not_reported_as_sent(monkeypatch, fake_http):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    fake_http(FakeResponse({"ok": False}))
    result = TOOL_FUNCTIONS["send"](text="Test", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert result.get("status") != "sent"


@pytest.mark.parametrize("reply", ["Đồng ý chuẩn bị", "Tôi đồng ý chuẩn bị. Chưa gửi nhé.", "Có, đồng ý chuẩn bị. Tôi chưa có nội dung.", "Yes, prepare the draft, not yet send it."])
def test_explicit_preparation_can_coexist_with_no_send_instruction(reply):
    state = {}
    advance_delivery(state, "Prepare a message")
    remember_clarification(state, {"stage": "prepare_send"})
    advance_delivery(state, reply)
    assert state["stage"] == "collecting"
    assert send_rejection(state, {"text": "draft", "confirmed": True})


def test_wrapped_timeout_is_classified_retryable_without_retrying_it():
    from tools._shared import err
    result = err("web_search", requests.ConnectionError("Connection aborted: TimeoutError(60, operation timed out)"))
    assert result["retryable"] is True


def test_missing_question_is_repaired_without_losing_preparation_state():
    state = prepared_state()
    provider = ScriptedProvider([
        response("clarify", response_type="text", stage="collect_send_text"),
        response("clarify", question="Bạn muốn gửi nội dung gì?", response_type="text", stage="collect_send_text"),
    ])
    result = run(provider, "Tôi chưa có nội dung; chưa gửi.", state)
    assert result["status"] == "waiting_for_user"
    assert state["stage"] == "collecting"
    assert result["tool_events"][0]["result"]["error"] == "ValueError"
    assert result["tool_events"][1]["result"]["awaiting_user"] is True


def test_empty_social_query_is_repaired_to_clarification_without_http(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "social_search", lambda **kw: calls.append(kw))
    provider = ScriptedProvider([
        response("social_search", query="", search_type="Latest"),
        response("clarify", question="Tài khoản nào?", response_type="text", stage="information"),
    ])
    result = run(provider, "Lấy tweet mới nhất giúp tôi.")
    assert result["status"] == "waiting_for_user"
    assert calls == []
    assert result["tool_events"][0]["result"]["error"] == "InvalidArguments"


def test_invented_fetch_url_is_not_requested(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "fetch", lambda **kw: calls.append(kw))
    provider = ScriptedProvider([
        response("fetch", url="https://invented.example/article"),
        response("clarify", question="Bạn gửi URL nhé?", response_type="text", stage="information"),
    ])
    result = run(provider, "Đọc bài viết đó giúp tôi.")
    assert result["status"] == "waiting_for_user"
    assert calls == []


def test_fetch_url_from_a_real_search_result_is_allowed(monkeypatch):
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "lookup", lambda **kw: {"items": [{"title": "A", "url": "https://example.org/a"}]})
    monkeypatch.setitem(TOOL_FUNCTIONS, "fetch", lambda **kw: calls.append(kw) or {"items": [{"title": "A", "url": kw["url"], "summary": "Source"}]})
    provider = ScriptedProvider([
        response("lookup", query="a", topic="general"),
        response("fetch", url="https://example.org/a"),
        response("finish_response", text="Source A: https://example.org/a", kind="answer"),
    ])
    result = run(provider, "Tìm và đọc nguồn về A.")
    assert result["status"] == "answered"
    assert calls == [{"url": "https://example.org/a"}]


def test_one_shot_evaluator_records_send_but_cannot_publish(monkeypatch):
    from agent import ResearchAgent
    calls = []
    monkeypatch.setitem(TOOL_FUNCTIONS, "send", lambda **kw: calls.append(kw))
    provider = ScriptedProvider([response("send", text="Unsafe", confirmed=True)])
    result = ResearchAgent(provider, system_prompt="test").run([{"role": "user", "content": "test"}])
    assert result.tool_calls[0].name == "send"
    assert result.tool_results[0]["result"]["error"] == "ActionExecutionDisabled"
    assert calls == []


def test_clarify_strict_schema_is_passed_to_the_provider():
    from pathlib import Path
    from tools import load_tool_declarations, to_openai_tools
    tools = to_openai_tools(load_tool_declarations(Path(__file__).resolve().parents[1] / "artifacts/tools.yaml"))
    clarify = next(t["function"] for t in tools if t["function"]["name"] == "clarify")
    assert clarify["strict"] is True
    schema = clarify["parameters"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


@pytest.mark.parametrize("text,expected", [
    ('Nội dung chính xác: Đây là bản tin. Chưa gửi.', 'Đây là bản tin.'),
    ('Nội dung: "Chưa gửi." Chưa gửi nhé.', 'Chưa gửi.'),
    ('Message: "A quoted message" Do not send.', 'A quoted message'),
    ('Nội dung là: “Đừng gửi.” Chưa gửi.', 'Đừng gửi.'),
    ('Không có nội dung cụ thể.', None),
])
def test_labeled_draft_separates_message_from_control_instructions(text, expected):
    from live_protocol import explicit_user_draft
    assert explicit_user_draft(text) == expected


def test_preview_cannot_include_a_trailing_do_not_send_instruction():
    from live_protocol import validate_clarification
    state = prepared_state()
    advance_delivery(state, 'Nội dung chính xác: Bản tin nhóm. Chưa gửi.')
    error = validate_clarification(state, {'stage': 'confirm_send', 'response_type': 'yes_no', 'draft_text': 'Bản tin nhóm. Chưa gửi.'})
    assert error and 'Bản tin nhóm.' in error
    assert validate_clarification(state, {'stage': 'confirm_send', 'response_type': 'yes_no', 'draft_text': 'Bản tin nhóm.'}) is None


def test_provider_failure_after_a_read_preserves_prior_tool_evidence(monkeypatch):
    class ReadThenFail:
        def __init__(self):
            self.n = 0
        def complete(self, *args, **kwargs):
            self.n += 1
            if self.n == 1:
                return response('lookup', query='research', topic='general')
            raise requests.Timeout('model response timed out')
    monkeypatch.setitem(TOOL_FUNCTIONS, 'lookup', lambda **kw: {'items': [{'title': 'A', 'url': 'https://example.org/a'}]})
    result = run(ReadThenFail())
    assert result['status'] == 'provider_error'
    assert result['tool_events'][0]['tool'] == 'lookup'
    assert result['rounds'][-1]['provider_error']['retryable'] is True
    assert 'chưa hoàn tất' in result['assistant_text']


def test_model_client_has_a_deadline_no_hidden_retry_and_is_closed(monkeypatch):
    import openai
    from types import SimpleNamespace
    from providers.openai_provider import OpenAIProvider
    captured = {}
    class Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='ok', tool_calls=[]))])))
        def __enter__(self):
            return self
        def __exit__(self, *args):
            captured['closed'] = True
    monkeypatch.setattr(openai, 'OpenAI', Client)
    monkeypatch.setenv('TEST_MODEL_KEY', 'fake-model-key')
    monkeypatch.delenv('MODEL_TIMEOUT_SECONDS', raising=False)
    result = OpenAIProvider(api_key_env='TEST_MODEL_KEY').complete([{'role': 'user', 'content': 'test'}])
    assert result.text == 'ok'
    assert captured['timeout'] == 60
    assert captured['max_retries'] == 0
    assert captured['closed'] is True
