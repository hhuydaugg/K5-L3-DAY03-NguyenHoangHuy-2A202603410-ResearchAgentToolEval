"""Streamlit UI: python -m streamlit run app.py"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st

from chat import execute_tool_call, run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"


def timestamp() -> str:
    return datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")


def new_session(model: str) -> dict:
    version = build_artifact_version("v3", ARTIFACTS / "system_prompt.md", ARTIFACTS / "tools.yaml")
    return {"transcript_id": f"v3_gemini_ui_{uuid4().hex}", **artifact_version_dict(version),
            "provider": "gemini", "model": model, "source": "streamlit_live",
            "created_at": timestamp(), "turns": []}


def redact(value):
    """Remove configured secrets from displayed/exported API error messages."""
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        for key, secret in os.environ.items():
            if secret and (key.endswith("_API_KEY") or key in {"RAPIDAPI_KEY", "TELEGRAM_BOT_TOKEN"}):
                value = value.replace(secret, "[REDACTED]")
    return value


def save_turn(user_text: str, result: dict) -> None:
    transcript = st.session_state.transcript
    transcript["turns"].append(redact({"turn_index": len(transcript["turns"]) + 1,
                                     "user": user_text, "ended_at": timestamp(), **result}))
    path = ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json"
    write_transcript(path, transcript)


def render_turn(turn: dict) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        if turn.get("status") == "provider_error":
            st.error(turn["assistant_text"])
        else:
            st.markdown(turn.get("assistant_text") or "Chưa có câu trả lời.")
        if turn.get("tool_events"):
            with st.expander("Nguồn và các bước đã thực hiện"):
                st.json(turn["tool_events"])


def offline_tools() -> None:
    st.subheader("Xử lý dữ liệu có sẵn")
    st.caption("Chạy trực tiếp bằng Python, không gọi model và không tốn quota API.")
    choice = st.radio("Công cụ", ["Loại link trùng", "Tạo bản tin", "Tra cứu policy"], horizontal=True)
    with st.form("offline_form"):
        if choice == "Tra cứu policy":
            query = st.text_input("Nội dung cần tra cứu", "source citation")
            area = st.selectbox("Nhóm chính sách", ["all", "ai_research", "source_citation", "data_privacy", "external_publishing", "tool_usage"])
        else:
            st.caption("Danh sách minh họa bên dưới là dữ liệu nhập sẵn, không phải kết quả tìm kiếm.")
            raw = st.text_area("Danh sách items (JSON)", value=json.dumps([
                {"title": "Nguồn A", "url": "https://example.com/a?utm_source=demo", "summary": "Nội dung minh họa."},
                {"title": "Bản trùng A", "url": "https://example.com/a"},
                {"title": "Nguồn B", "url": "https://example.com/b"},
            ], ensure_ascii=False, indent=2), height=245)
            if choice == "Tạo bản tin":
                template = st.selectbox("Cách trình bày", ["sections", "brief", "bullets", "thread", "daily_ai_vn"])
                headline = st.text_input("Tiêu đề", "Bản tin nghiên cứu")
        submitted = st.form_submit_button("Chạy công cụ", type="primary")
    if submitted:
        try:
            if choice == "Tra cứu policy":
                result = TOOL_FUNCTIONS["policy"](query=query, policy_area=area)
            else:
                items = json.loads(raw)
                if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                    raise ValueError("Items phải là một danh sách các object JSON.")
                if choice == "Loại link trùng":
                    result = TOOL_FUNCTIONS["deduplicate"](items=items)
                else:
                    result = TOOL_FUNCTIONS["format"](items=items, template=template, headline=headline)
            if result.get("error"):
                st.error(result.get("message", result["error"]))
            else:
                if "removed_count" in result:
                    st.success(f"Còn {result['item_count']} mục; đã loại {result['removed_count']} link trùng.")
                if result.get("markdown"):
                    st.markdown(result["markdown"])
                st.json(result)
        except (ValueError, TypeError, AttributeError) as exc:
            st.error(f"Dữ liệu chưa hợp lệ: {exc}")


def evidence() -> None:
    st.subheader("Kết quả đã ghi nhận")
    runs = sorted((ROOT / "runs").glob("*.json"), reverse=True)
    if not runs:
        st.info("Chưa có run đánh giá. Chạy run_eval.py để ghi nhận kết quả thật.")
        return
    selected = st.selectbox("Run đánh giá", runs, format_func=lambda path: path.name)
    run = json.loads(selected.read_text(encoding="utf-8"))
    summary = run["summary"]
    a, b, c = st.columns(3)
    a.metric("Case đã đo", f"{summary['measured_cases']}/{summary['total_cases']}")
    b.metric("Case đạt", summary["passed_cases"])
    c.metric("Độ chính xác trên case đã đo", f"{summary['case_accuracy']:.1%}")
    if summary["provider_error_cases"]:
        st.warning(f"{summary['provider_error_cases']} case lỗi provider và bị loại khỏi mẫu số. Đây là kết quả chưa đầy đủ.")
    st.dataframe([{"Case": row["id"], "Kết quả": "PASS" if row["result"]["passed"] else "FAIL",
                   "Loại lỗi": row["result"].get("failure_type") or ""} for row in run["results"]], hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Research Desk", page_icon="🔎", layout="wide")
    load_lab_env(ROOT)
    st.markdown("<style>.block-container{max-width:1150px;padding-top:2rem}"
                "h1{letter-spacing:-.04em}div[data-testid=stMetric]{padding:1rem;border:1px solid #dce5e1;border-radius:12px}"
                "</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### Research Desk")
        st.caption("Research Agent · v3 prepared")
        model = st.text_input("Gemini model", value="gemini-3.5-flash")
        for env, label in [("GEMINI_API_KEY", "Gemini"), ("TAVILY_API_KEY", "Tìm web"),
                           ("FIRECRAWL_API_KEY", "Đọc URL"), ("RAPIDAPI_KEY", "X / Twitter")]:
            st.caption(f"{'✓' if os.getenv(env) else '○'} {label}: {'đã cấu hình' if os.getenv(env) else 'chưa cấu hình'}")
        st.caption("Đã cấu hình key chưa đồng nghĩa còn quota hoặc đủ quyền API.")
        if st.button("Phiên mới") or ("transcript" in st.session_state and st.session_state.transcript["model"] != model):
            st.session_state.transcript = new_session(model)
            st.session_state.pending_action = None
        if "transcript" not in st.session_state:
            st.session_state.transcript = new_session(model)
        st.download_button("Tải transcript JSON", json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2),
                           file_name=f"{st.session_state.transcript['transcript_id']}.transcript.json", mime="application/json")
    st.caption("TÌM HIỂU · ĐỐI CHIẾU · TỔNG HỢP")
    st.title("Từ nguồn tin đến bản tin.")
    st.markdown("Tìm trên web, đọc bài viết, theo dõi X và tổng hợp nguồn thành digest có trích dẫn.")
    chat_tab, local_tab, eval_tab = st.tabs(["Trò chuyện", "Công cụ offline", "Kết quả đánh giá"])
    with local_tab:
        offline_tools()
    with eval_tab:
        evidence()
    with chat_tab:
        transcript = st.session_state.transcript
        if not transcript["turns"]:
            st.info("Thử: “Tìm 3 tin tức về robotics trong tuần này” hoặc “Quy định nội bộ về trích dẫn nguồn là gì?”")
        for turn in transcript["turns"]:
            render_turn(turn)
        pending = st.session_state.get("pending_action")
        if pending:
            st.warning("Chỉ gửi khi bạn xác nhận nội dung bên dưới.")
            st.markdown(pending["args"]["text"])
            yes, no = st.columns(2)
            if yes.button("Xác nhận gửi Telegram", type="primary"):
                event = execute_tool_call(ToolCall(**pending), allow_send=True)
                success = event["result"].get("status") == "sent"
                save_turn("Xác nhận gửi đúng nội dung đã xem.", {"status": "answered" if success else "tool_error",
                          "assistant_text": "Đã gửi lên Telegram." if success else "Chưa gửi được. Xem kết quả tool để biết lỗi.",
                          "rounds": [], "tool_events": [event]})
                st.session_state.pending_action = None
                st.rerun()
            if no.button("Hủy gửi"):
                save_turn("Hủy gửi.", {"status": "answered", "assistant_text": "Đã hủy gửi.", "rounds": [], "tool_events": []})
                st.session_state.pending_action = None
                st.rerun()
        user_text = st.chat_input("Bạn muốn tìm hiểu điều gì?", disabled=not bool(os.getenv("GEMINI_API_KEY")))
        if user_text:
            # A new request/correction cancels any older pending action.
            st.session_state.pending_action = None
            history = []
            for turn in transcript["turns"]:
                if turn.get("status") != "provider_error":
                    history.extend([{"role": "user", "content": turn["user"]},
                                    {"role": "assistant", "content": turn.get("assistant_text", "")}])
            messages = [{"role": "system", "content": (ARTIFACTS / "system_prompt.md").read_text(encoding="utf-8")},
                        *trim_history(history, 5), {"role": "user", "content": user_text}]
            try:
                if "provider" not in st.session_state:
                    st.session_state.provider = make_provider("gemini")
                with st.spinner("Đang tra cứu; nếu API yêu cầu chờ, chương trình sẽ tự thử lại…"):
                    result = run_model_tool_loop(provider=st.session_state.provider, messages=messages,
                        tools=to_openai_tools(load_tool_declarations(ARTIFACTS / "tools.yaml")), model=model, max_tool_rounds=4)
                st.session_state.pending_action = result.get("pending_action")
            except Exception as exc:
                result = {"status": "provider_error", "assistant_text": f"Chưa gọi được Gemini: {exc}",
                          "rounds": [], "tool_events": []}
            save_turn(user_text, result)
            st.rerun()


if __name__ == "__main__":
    main()
