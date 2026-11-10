---
name: filter
track: core
kind: local_formatter
provider: local Python
requires_env: []
inputs: [items, query]
outputs: [items, query, input_count, item_count]
side_effect: false
---
# filter

Keep existing research items whose title, summary, URL, or source contains `query`.
Matching is case-insensitive and ignores Vietnamese diacritics. Does not search the
web, fetch URLs, or invent items. Empty or missing `query`, and malformed `items`,
return an error dictionary. Input objects are not modified.
