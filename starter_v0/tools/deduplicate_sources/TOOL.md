---
name: deduplicate_sources
track: core
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, item_count, removed_count, error, message]
side_effect: false
---
# deduplicate_sources

Remove exact duplicate HTTP(S) URLs from supplied source objects, retaining the first item and input order. Strip surrounding URL whitespace only; keep query strings, fragments, case and trailing slashes distinct. Metadata is copied; input is not mutated. Empty lists succeed. Missing/non-list input, non-object entries and invalid URLs return an error dict, with no partial successful result. Unexpected parsing failures also return an error dict. No network, model, credentials or writes are used. This is not a semantic duplicate detector and does not establish source credibility.
