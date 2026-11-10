from __future__ import annotations

from typing import Any

from tools._shared import err


def ask_user(question: str = "", response_type: str = "text", options: list[str] | None = None,
             stage: str = "information", draft_text: str = "") -> dict[str, Any]:
    try:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be nonempty text")
        if response_type not in {"text", "yes_no", "choice"}:
            raise ValueError("invalid response_type")
        if stage not in {"information", "prepare_send", "collect_send_text", "confirm_send"}:
            raise ValueError("invalid clarification stage")
        if response_type == "choice" and (not isinstance(options, list) or not options or any(not isinstance(x, str) or not x.strip() for x in options)):
            raise ValueError("choice needs nonempty text options")
        if stage in {"prepare_send", "confirm_send"} and response_type != "yes_no":
            raise ValueError("send consent stages require yes_no")
        if stage == "collect_send_text" and response_type != "text":
            raise ValueError("collect_send_text requires text")
        if stage == "confirm_send":
            if not isinstance(draft_text, str) or not draft_text.strip():
                raise ValueError("confirm_send requires exact draft_text")
            question = ("Nội dung:\n" + draft_text + "\n\nĐích gửi: kênh Telegram đã cấu hình.\n"
                        "Bạn xác nhận gửi đúng nội dung này đến kênh đã cấu hình không?")
        return {"tool": "ask_user", "question": question, "response_type": response_type,
                "options": options or [], "awaiting_user": True, "stage": stage,
                **({"draft_text": draft_text} if stage == "confirm_send" else {})}
    except Exception as exc:
        return err("ask_user", exc)
