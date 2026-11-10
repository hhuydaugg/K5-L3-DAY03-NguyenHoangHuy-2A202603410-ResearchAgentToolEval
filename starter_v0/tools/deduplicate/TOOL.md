---
name: deduplicate
track: core
kind: local_formatter
provider: local Python
requires_env: []
inputs: [items]
outputs: [items, input_count, item_count, removed_count]
side_effect: false
---
# deduplicate

Remove duplicate research items by URL before formatting a digest, or when the
user explicitly asks to remove duplicate links. No API key or network required.
Use only items already supplied by the user or returned by tools; this tool does
not find new sources, compare factual claims, or verify a site's authenticity.

Comparison ignores URL fragments, `utm_*`, `fbclid`, and `gclid`; it sorts query
parameters and normalizes scheme/host case. It preserves path case, scheme,
meaningful query values, and the first item's original text and URL. Items without
URLs are kept separately, since identical titles do not prove identical sources.

`items=[]` returns an empty result. Missing input, non-object items, invalid URLs,
and unexpected errors return an error dictionary. Input objects are not modified.
