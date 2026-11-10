"""CLI chat must handle Vietnamese tool results on Windows terminals."""
from pathlib import Path


def test_chat_configures_utf8_output_before_printing_vietnamese() -> None:
    source = (Path(__file__).resolve().parents[1] / "chat.py").read_text(encoding="utf-8")
    assert 'sys.stdout.reconfigure(encoding="utf-8", errors="replace")' in source
    assert 'sys.stderr.reconfigure(encoding="utf-8", errors="replace")' in source
