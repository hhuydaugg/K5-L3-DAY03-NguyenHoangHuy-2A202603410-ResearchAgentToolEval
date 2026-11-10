# Tool Folder Contract

Each tool lives in its own folder:

```text
tools/<tool_name>/
  TOOL.md   # frontmatter + human notes
  tool.py   # self-contained implementation
```

`tools/__init__.py` is the registry. `agent.py`, `chat.py`, and `run_eval.py`
import `TOOL_FUNCTIONS` from that registry.

## Frontmatter Fields

Every `TOOL.md` uses the same fields:

```yaml
---
name: tool_name
track: core | bonus
kind: live_api | local_formatter | local_knowledge | action | control
provider: Provider name if any
requires_env: [ENV_VAR]
inputs: [arg_name]
outputs: [field_name]
side_effect: false | true | local_file_write
requires_confirmation: true   # only for write/action tools
---
```

Core tools are enough to pass the base lab. Bonus tools are for teams that want
extra scope, extra eval cases, or a live delivery action.


## Shared failures and live execution

Errors include error/message plus status_code and retryable when available. Secret values in errors, including Telegram bot URLs, are redacted. Fetch rejects explicit target HTTP error metadata and empty content; unmarked soft error pages still need review.

The one-shot ResearchAgent/evaluator grades proposed send calls but never executes posting. CLI/UI use live_protocol.py: required tool replies plus an internal finish_response terminal tool, per-session preparation/final-consent state, exact preview/destination checks, bounded repairs and source-error termination. Live protocol/runtime/tool hashes are included in transcripts. Live guard success is not raw-model routing accuracy.

Strict clarify schemas require question, response_type, options, stage and draft_text. Use empty options/draft_text outside choice/final preview. Legacy direct Python calls default to information/text. prepare_send and confirm_send require yes_no; collect_send_text requires text. Final preview shows the exact message and configured Telegram destination; no arbitrary channel selection is supported.

The OpenAI-compatible adapter defaults to a 60-second deadline, closes its client, and does not retry implicitly. Set a positive MODEL_TIMEOUT_SECONDS to override. API-tested provider: OpenRouter/openai/gpt-4o-mini; other providers may enforce schemas differently. Strict schema reference: https://developers.openai.com/api/docs/guides/function-calling .
