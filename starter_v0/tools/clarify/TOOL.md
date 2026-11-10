---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options, stage, draft_text]
outputs: [question, response_type, options, awaiting_user, stage, draft_text, error, message]
side_effect: false
---
# clarify

Returns a question to the user and pauses until the next user turn.
`response_type` is free text, yes/no, or a choice from `options`.

Stages: information (ordinary missing detail), prepare_send (yes_no), collect_send_text (text after preparation consent), confirm_send (yes_no with exact draft_text). The final stage builds a full preview for the configured Telegram channel. Live runtime separately validates consent/order, exact text and destination continuity; this control tool alone does not send anything. Legacy direct calls default to information/text. Bad input returns an error dict.
