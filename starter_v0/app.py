"""Streamlit UI for the Research Agent. Run: streamlit run app.py"""
from __future__ import annotations

import sys
from datetime import datetime

import streamlit as st

# chat.py prints emoji; Windows server stdout defaults to cp1252 and would raise UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8")

from chat import ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"

st.set_page_config(page_title="Research Agent", page_icon="🔎")

with st.sidebar:
    provider_name = st.selectbox("Provider", ["openai", "openrouter", "gemini", "anthropic", "ollama"])
    model = st.text_input("Model (để trống = mặc định của provider)").strip() or None
    version = st.text_input("Version label", "v0").strip() or "v0"
    history_window = st.number_input("History window (cặp lượt)", 0, 20, 5)
    max_tool_rounds = st.number_input("Max tool rounds", 1, 8, 4)
    if st.button("Cuộc chat mới"):
        st.session_state.clear()
        st.rerun()

if "turns" not in st.session_state:
    artifact_version = build_artifact_version(version, PROMPT_PATH, TOOLS_PATH)
    provider = make_provider(provider_name)
    transcript_id = "_".join(["ui", safe_slug(version), safe_slug(provider_name), datetime.now().strftime("%Y%m%dT%H%M%S%f")])
    # Load prompt/tools once per session (like chat.py) so transcript hashes match what the model actually saw.
    st.session_state.update(
        system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=to_openai_tools(load_tool_declarations(TOOLS_PATH)),
        turns=[],
        history=[],
        transcript_path=ROOT / "transcripts" / f"{transcript_id}.transcript.json",
        transcript={
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact_version),
            "provider": provider_name,
            "model": model or getattr(provider, "default_model", None),
            "system_prompt": str(PROMPT_PATH),
            "tools": str(TOOLS_PATH),
            "history_window": history_window,
            "max_tool_rounds": max_tool_rounds,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        },
    )

transcript = st.session_state.transcript
st.title("🔎 Research Agent")
st.caption(f"artifact_version `{transcript['artifact_version']}` · {transcript['provider']} / {transcript['model']}")


def show_tools(turn: dict) -> None:
    for rnd in turn.get("rounds", []):
        for event in rnd.get("tool_results", []):
            with st.expander(f"🔧 {event['tool']}"):
                st.json({"args": event.get("args"), "result": event.get("result")}, expanded=False)


for turn in st.session_state.turns:
    st.chat_message("user").write(turn["user"])
    with st.chat_message("assistant"):
        show_tools(turn)
        st.markdown(turn.get("assistant_text") or turn.get("error") or "")

user_text = st.chat_input("Hỏi agent: tin AI hôm nay, tweet của @sama, tóm tắt một URL...")
if user_text:
    st.chat_message("user").write(user_text)
    turn = {"turn_index": len(st.session_state.turns) + 1, "started_at": now_iso(), "user": user_text}
    with st.chat_message("assistant"), st.spinner("Agent đang chạy tool..."):
        try:
            result = run_model_tool_loop(
                provider=make_provider(transcript["provider"]),
                messages=[
                    {"role": "system", "content": st.session_state.system_prompt},
                    *trim_history(st.session_state.history, int(history_window)),
                    {"role": "user", "content": user_text},
                ],
                tools=st.session_state.tools,
                model=model,
                max_tool_rounds=int(max_tool_rounds),
            )
            turn.update(result)
            st.session_state.history += [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": result["assistant_text"]},
            ]
        except Exception as exc:  # show provider errors in the UI instead of crashing the page
            turn.update(status="provider_error", error=f"{type(exc).__name__}: {exc}")
        show_tools(turn)
        st.markdown(turn.get("assistant_text") or turn.get("error") or "")
    turn["ended_at"] = now_iso()
    st.session_state.turns.append(turn)
    transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, transcript)
