---
name: sources
track: core
kind: local_formatter
provider: local Python
requires_env: []
inputs: [items]
outputs: [sources, source_count, input_count]
side_effect: false
---
# sources

List unique source domains from existing research items, first-seen order. Prefers
the URL host (`www.` stripped); if there is no URL, uses the `source` field. Does
not search or fetch. Malformed `items` return an error dictionary.
