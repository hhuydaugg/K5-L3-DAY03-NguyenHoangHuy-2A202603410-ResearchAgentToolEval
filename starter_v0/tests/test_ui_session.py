"""Offline UI integration: tool results, transcript persistence and config isolation."""
from pathlib import Path
import json

from streamlit.testing.v1 import AppTest

from providers.base import ModelResponse, ToolCall


class ClarifyThenCancelProvider:
    default_model = "offline-ui-test"

    def complete(self, messages, tools=None, **kwargs):
        if "hủy" in messages[-1]["content"].lower():
            return ModelResponse(text="Đã hủy yêu cầu; không gửi gì.", tool_calls=[])
        return ModelResponse(text=None, tool_calls=[ToolCall("clarify", {
            "question": "Bạn muốn xem tài khoản nào?", "response_type": "text"
        })])


def test_ui_logs_clarification_and_cancellation_without_send(monkeypatch, tmp_path):
    import chat
    import providers
    monkeypatch.setattr(chat, "ROOT", tmp_path)
    monkeypatch.setattr(providers, "make_provider", lambda name: ClarifyThenCancelProvider())
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert not app.exception
    app.chat_input[0].set_value("Tóm tắt tweet mới nhất.").run()
    assert not app.exception
    app.chat_input[0].set_value("Tôi hủy yêu cầu.").run()
    assert not app.exception
    paths = list((tmp_path / "transcripts").glob("*.json"))
    assert len(paths) == 1
    transcript = json.loads(paths[0].read_text())
    assert transcript["version"] == "v2"
    assert len(transcript["turns"]) == 2
    assert transcript["turns"][0]["status"] == "waiting_for_user"
    events = [e for turn in transcript["turns"] for e in turn["tool_events"]]
    assert [e["tool"] for e in events] == ["clarify"]
    assert "hủy" in transcript["turns"][1]["assistant_text"]


def test_ui_configuration_change_starts_a_separate_transcript(monkeypatch, tmp_path):
    import chat
    import providers
    monkeypatch.setattr(chat, "ROOT", tmp_path)
    monkeypatch.setattr(providers, "make_provider", lambda name: ClarifyThenCancelProvider())
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.chat_input[0].set_value("Tóm tắt tweet mới nhất.").run()
    original = app.session_state["transcript_path"]
    app.sidebar.text_input[0].set_value("different-model").run()
    assert not app.exception
    assert app.session_state["transcript_path"] != original
    assert app.session_state["history"] == []
    assert app.session_state["transcript"]["model"] == "different-model"
    assert json.loads(original.read_text())["model"] == "offline-ui-test"
