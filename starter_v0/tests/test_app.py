"""Exercise browser UI flows offline with Streamlit's application runner."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

import chat
import providers
from conftest import FakeResponse
from providers.base import ModelResponse, ToolCall

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def ui(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("GEMINI_API_KEY=fake-gemini-key\n", encoding="utf-8")
    monkeypatch.setenv("DAY04_ENV_FILE", str(env))
    factory = MagicMock()
    monkeypatch.setattr(providers, "make_provider", factory)
    writer = MagicMock()
    monkeypatch.setattr(chat, "write_transcript", writer)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    return app, factory, writer


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_offline_deduplicate_works_without_model(ui):
    app, factory, writer = ui
    button(app, "Chạy công cụ").click().run()
    assert not app.exception
    assert any("đã loại 1 link trùng" in item.value for item in app.success)
    factory.assert_not_called()
    writer.assert_not_called()


def test_invalid_json_is_a_visible_input_error(ui):
    app, factory, _ = ui
    app.text_area[0].set_value("{bad-json")
    button(app, "Chạy công cụ").click().run()
    assert not app.exception
    assert any("Dữ liệu chưa hợp lệ" in item.value for item in app.error)
    factory.assert_not_called()


def test_offline_policy_works_without_model(ui):
    app, factory, _ = ui
    app.radio[0].set_value("Tra cứu policy").run()
    button(app, "Chạy công cụ").click().run()
    assert not app.exception
    assert any("search_company_policy" in str(item.value) for item in app.json)
    factory.assert_not_called()


def test_clarification_is_saved_as_a_real_ui_turn(ui):
    app, factory, writer = ui
    factory.return_value.complete.return_value = ModelResponse(tool_calls=[
        ToolCall("clarify", {"question": "Bạn muốn đọc URL nào?", "response_type": "text"}),
    ])
    app.chat_input[0].set_value("Đọc bài này giúp tôi").run()
    assert not app.exception
    transcript = app.session_state["transcript"]
    assert len(transcript["turns"]) == 1
    assert transcript["turns"][0]["status"] == "waiting_for_user"
    assert transcript["turns"][0]["assistant_text"] == "Bạn muốn đọc URL nào?"
    assert transcript["source"] == "streamlit_live"
    assert "prompt_hash" in transcript and "tools_hash" in transcript
    assert writer.call_args.args[0].suffix == ".json"
    factory.return_value.complete.assert_called_once()


@pytest.mark.parametrize("confirm", [False, True])
def test_send_requires_separate_ui_button(ui, monkeypatch, fake_http, confirm):
    app, factory, _ = ui
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    factory.return_value.complete.return_value = ModelResponse(tool_calls=[
        ToolCall("send", {"text": "Exact draft", "confirmed": True}),
    ])
    app.chat_input[0].set_value("Gửi bản tin").run()
    assert not app.exception
    assert calls == []
    assert app.session_state["pending_action"]["args"]["text"] == "Exact draft"
    button(app, "Xác nhận gửi Telegram" if confirm else "Hủy gửi").click().run()
    assert not app.exception
    assert app.session_state["pending_action"] is None
    assert len(calls) == int(confirm)
    if confirm:
        assert calls[0]["json"]["text"] == "Exact draft"
    factory.return_value.complete.assert_called_once()


def test_error_does_not_expose_configured_key(ui):
    app, factory, writer = ui
    factory.return_value.complete.side_effect = RuntimeError("invalid fake-gemini-key")
    app.chat_input[0].set_value("Tìm tin AI").run()
    assert not app.exception
    turn = app.session_state["transcript"]["turns"][0]
    assert turn["status"] == "provider_error"
    assert "fake-gemini-key" not in turn["assistant_text"]
    assert "[REDACTED]" in turn["assistant_text"]
    writer.assert_called_once()
